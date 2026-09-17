"""Client deals are paid individually and never disclose another owner's records."""

from datetime import timedelta
from uuid import uuid4

import pytest

from munipal.api.routes.auth import _create_token
from munipal.core.models import User

BASE = "/api/v1/register"


def headers(user, kind="access"):
    return {"Authorization": "Bearer " + _create_token(user.id, kind, timedelta(minutes=5))}


@pytest.fixture
async def people(db_session):
    users = [
        User(
            id=str(uuid4()),
            email=f"portal-{i}@example.test",
            hashed_password="unused",
            organization=f"tenant-{i}",
            is_active=True,
            is_superuser=i == 2,
        )
        for i in range(3)
    ]
    db_session.add_all(users)
    await db_session.commit()
    return users


async def create(client, user):
    r = await client.post(
        BASE + "/deals",
        headers=headers(user),
        json={
            "name": "2025 Housing Bonds",
            "legal_name": "Example Housing LLC",
            "bonds_already_closed": True,
            "entity_type": "private_obligated_person",
            "professional_contact": "Our bond counsel",
            "privacy_consent": True,
        },
    )
    assert r.status_code == 201, r.text
    return r.json()["id"]


async def test_strict_identity_and_eligibility(test_client, people, db_session):
    user = people[0]
    for auth in ({}, {"X-User-Id": user.id}, headers(user, "refresh")):
        r = await test_client.get(BASE + "/deals", headers=auth)
        assert r.status_code == 401
        assert r.headers["cache-control"] == "no-store"
    assert (await test_client.get(BASE + "/deals", headers=headers(user))).json() == []
    for field, value in (
        ("bonds_already_closed", False),
        ("entity_type", "municipal_entity"),
        ("privacy_consent", False),
    ):
        payload = {
            "name": "Deal",
            "legal_name": "Borrower",
            "bonds_already_closed": True,
            "entity_type": "private_obligated_person",
            "privacy_consent": True,
            "professional_contact": "Counsel",
        }
        payload[field] = value
        assert (
            await test_client.post(BASE + "/deals", headers=headers(user), json=payload)
        ).status_code == 422
    user.is_active = False
    await db_session.commit()
    assert (await test_client.get(BASE + "/deals", headers=headers(user))).status_code == 403


async def test_intake_quote_payment_reports_and_isolation(
    test_client, people, db_session, monkeypatch
):
    from munipal.core.models.register import RegisterDeal
    from munipal.services.register_billing import fulfill_register_checkout

    owner, stranger, operator = people
    deal_id = await create(test_client, owner)
    path = BASE + "/deals/" + deal_id
    for method, suffix in (("GET", ""), ("POST", "/build"), ("POST", "/checkout")):
        assert (
            await test_client.request(method, path + suffix, headers=headers(stranger))
        ).status_code == 404
    assert (await test_client.post(path + "/build", headers=headers(owner))).status_code == 402
    assert (
        await test_client.put(
            path + "/quote",
            headers=headers(owner),
            json={"amount_cents": 125000, "note": "One deal"},
        )
    ).status_code == 403
    uploaded = await test_client.post(
        path + "/documents",
        headers=headers(owner),
        files={
            "file": (
                "CDA.txt",
                b"Section 4. Annual reporting\nThe Borrower shall deliver an annual report within 180 days.",
                "text/plain",
            )
        },
    )
    assert uploaded.status_code == 201, uploaded.text
    document_id = uploaded.json()["id"]
    assert (
        await test_client.get(path + f"/documents/{document_id}", headers=headers(stranger))
    ).status_code == 404
    assert (
        await test_client.put(
            path + "/quote",
            headers=headers(operator),
            json={
                "amount_cents": 125000,
                "note": "One closed deal; candidate map and skill package.",
            },
        )
    ).status_code == 200
    deal = await db_session.get(RegisterDeal, deal_id)
    deal.checkout_session_id = "cs_deal"
    await db_session.commit()
    event = {
        "id": "cs_deal",
        "mode": "payment",
        "payment_status": "unpaid",
        "amount_total": 125000,
        "currency": "usd",
        "payment_intent": "pi_deal",
        "metadata": {
            "register_deal_id": deal_id,
            "register_quote_version": str(deal.quote_version),
            "munipal_user_id": owner.id,
        },
    }
    await fulfill_register_checkout(db_session, event)
    assert deal.payment_status != "paid"
    event["payment_status"] = "paid"
    await fulfill_register_checkout(db_session, event)
    await fulfill_register_checkout(db_session, event)
    assert deal.payment_status == "paid"
    assert owner.subscription_tier != "subscription"
    result = await test_client.post(path + "/build", headers=headers(owner))
    assert result.status_code == 201, result.text
    report_id = result.json()["id"]
    detail = (await test_client.get(path, headers=headers(owner))).json()
    assert len(detail["reports"]) == 1
    assert detail["reports"][0]["candidate_count"] == 1
    assert (
        await test_client.get(path + f"/reports/{report_id}", headers=headers(stranger))
    ).status_code == 404
    download = await test_client.get(path + f"/reports/{report_id}", headers=headers(owner))
    assert download.status_code == 200
    import io
    import zipfile

    with zipfile.ZipFile(io.BytesIO(download.content)) as bundle:
        csv_text = bundle.read("candidate-map.csv").decode()
        assert "within 180 days" in csv_text
        assert "SKILL.md" in bundle.namelist()
        assert "2025-" not in csv_text
    second = await create(test_client, owner)
    assert (
        await test_client.post(BASE + f"/deals/{second}/build", headers=headers(owner))
    ).status_code == 402
    owner.organization = "moved-tenant"
    await db_session.commit()
    assert (await test_client.get(path, headers=headers(owner))).status_code == 404


async def test_folder_links_are_intake_not_fetches(test_client, people):
    path = BASE + "/deals/" + await create(test_client, people[0])
    auth = headers(people[0])
    for url in (
        "http://127.0.0.1",
        "https://drive.google.com.evil.test/folder",
        "javascript:alert(1)",
    ):
        assert (
            await test_client.post(path + "/folders", headers=auth, json={"url": url})
        ).status_code == 422
    r = await test_client.post(
        path + "/folders",
        headers=auth,
        json={"url": "https://drive.google.com/drive/folders/example"},
    )
    assert r.status_code == 201
    assert r.json()["status"] == "awaiting_import"


@pytest.fixture
async def quoted(test_client, people, db_session):
    from munipal.core.models.register import RegisterDeal

    deal_id = await create(test_client, people[0])
    deal = await db_session.get(RegisterDeal, deal_id)
    deal.payment_status = "awaiting_payment"
    deal.amount_cents = 10000
    deal.quote_version = 1
    deal.checkout_session_id = "cs_checkout"
    await db_session.commit()
    return deal


def payment(deal):
    return {
        "id": deal.checkout_session_id,
        "mode": "payment",
        "payment_status": "paid",
        "amount_total": deal.amount_cents,
        "currency": "usd",
        "payment_intent": "pi_order",
        "metadata": {
            "register_deal_id": deal.id,
            "munipal_user_id": deal.owner_id,
            "register_quote_version": str(deal.quote_version),
        },
    }


@pytest.mark.parametrize(
    "field,value",
    [
        ("id", "cs_other"),
        ("mode", "subscription"),
        ("payment_status", "unpaid"),
        ("amount_total", 10),
        ("currency", "eur"),
        ("payment_intent", None),
    ],
)
async def test_payment_must_match_quote(quoted, db_session, field, value):
    from munipal.services.register_billing import fulfill_register_checkout

    event = payment(quoted)
    event[field] = value
    await fulfill_register_checkout(db_session, event)
    assert quoted.payment_status == "awaiting_payment"


@pytest.mark.parametrize("field", ["munipal_user_id", "register_quote_version"])
async def test_payment_metadata_must_match(quoted, db_session, field):
    from munipal.services.register_billing import fulfill_register_checkout

    event = payment(quoted)
    event["metadata"][field] = "wrong"
    await fulfill_register_checkout(db_session, event)
    assert quoted.payment_status == "awaiting_payment"


@pytest.mark.parametrize("refund_first", [True, False])
async def test_full_refund_revokes_even_out_of_order(quoted, db_session, refund_first):
    from munipal.services.register_billing import fulfill_register_checkout, refund_register_payment

    event = payment(quoted)
    refund = {"payment_intent": "pi_order", "refunded": True}
    if refund_first:
        await refund_register_payment(db_session, refund)
    await fulfill_register_checkout(db_session, event)
    await refund_register_payment(db_session, refund)
    await fulfill_register_checkout(db_session, event)
    assert quoted.payment_status == "refunded"


async def test_signed_webhook_routes_one_time_purchase_without_subscription(
    test_client, people, quoted, monkeypatch
):
    from munipal.api.routes import stripe as route

    monkeypatch.setattr(
        route.stripe.Webhook,
        "construct_event",
        lambda *a: {"type": "checkout.session.completed", "data": {"object": payment(quoted)}},
    )
    response = await test_client.post("/api/v1/stripe/webhook", content=b"{}")
    assert response.status_code == 200
    assert quoted.payment_status == "paid"
    assert people[0].subscription_tier != "subscription"


async def test_checkout_uses_server_quote_and_stable_idempotency(
    test_client, people, quoted, db_session, monkeypatch
):
    from types import SimpleNamespace

    from munipal.api.routes import register_portal as route
    from munipal.config import get_settings

    quoted.checkout_session_id = None
    await db_session.commit()
    settings = get_settings()
    monkeypatch.setattr(settings, "stripe_secret_key", "sk_test_fake")
    monkeypatch.setattr(settings, "stripe_webhook_secret", "whsec_fake")
    calls = []
    session = SimpleNamespace(
        id="cs_new", url="https://checkout.stripe.com/c/pay/test", status="open"
    )

    def fake_create(**kwargs):
        calls.append(kwargs)
        return session

    monkeypatch.setattr(route.stripe.checkout.Session, "create", fake_create)
    monkeypatch.setattr(route.stripe.checkout.Session, "retrieve", lambda *a, **k: session)
    url = BASE + f"/deals/{quoted.id}/checkout"
    for _ in range(2):
        result = await test_client.post(url, headers=headers(people[0]), json={"amount_cents": 1})
        assert result.status_code == 200
    assert len(calls) == 1
    assert calls[0]["line_items"][0]["price_data"]["unit_amount"] == 10000
    assert calls[0]["mode"] == "payment"
    assert calls[0]["idempotency_key"] == f"register-{quoted.id}-1"
    assert (
        await test_client.put(
            BASE + f"/deals/{quoted.id}/quote",
            headers=headers(people[2]),
            json={"amount_cents": 20000, "note": "changed"},
        )
    ).status_code == 409


async def test_folder_blocks_build_and_operator_delivery_is_private(
    test_client, people, quoted, db_session
):
    import io
    import zipfile

    quoted.payment_status = "paid"
    await db_session.commit()
    path = BASE + f"/deals/{quoted.id}"
    owner, stranger, operator = people
    await test_client.post(
        path + "/documents",
        headers=headers(owner),
        files={"file": ("CDA.txt", b"The Borrower shall deliver annual reports.")},
    )
    folder = (
        await test_client.post(
            path + "/folders",
            headers=headers(owner),
            json={"url": "https://drive.google.com/drive/folders/abc"},
        )
    ).json()
    assert (await test_client.post(path + "/build", headers=headers(owner))).status_code == 409
    patch = {"status": "imported", "note": "Imported CDA.txt and checked pack."}
    assert (
        await test_client.patch(
            path + f"/folders/{folder['id']}", headers=headers(owner), json=patch
        )
    ).status_code == 403
    assert (
        await test_client.patch(
            path + f"/folders/{folder['id']}", headers=headers(operator), json=patch
        )
    ).status_code == 200
    first = (await test_client.post(path + "/build", headers=headers(owner))).json()
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr(
            "register.csv", "obligation,approval_ref\nAnnual report,Written approval 1\n"
        )
    payload = {"file": ("delivery.zip", buffer.getvalue(), "application/zip")}
    assert (
        await test_client.post(
            path + "/deliveries", headers=headers(owner), files=payload, data={"note": "Reviewed"}
        )
    ).status_code == 403
    delivery = await test_client.post(
        path + "/deliveries",
        headers=headers(operator),
        files=payload,
        data={"note": "Approved inputs reference 1"},
    )
    assert delivery.status_code == 201, delivery.text
    assert delivery.json()["version"] == 2 and delivery.json()["kind"] == "team_delivery"
    assert (
        await test_client.get(path + f"/reports/{first['id']}", headers=headers(owner))
    ).status_code == 200
    assert (
        await test_client.get(path + f"/reports/{delivery.json()['id']}", headers=headers(stranger))
    ).status_code == 404
