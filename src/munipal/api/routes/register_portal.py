"""Authenticated Obligation Register back office and client workspace."""

import io
import re
import zipfile
from pathlib import PurePosixPath
from typing import Literal
from urllib.parse import urlparse
from uuid import UUID

import stripe
from fastapi import APIRouter, Form, HTTPException, Query, Response, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.exceptions import RequestValidationError
from fastapi.routing import APIRoute
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import func, select
from sqlalchemy.orm import undefer

from munipal.api.dependencies import DbSession, StrictUser
from munipal.config import get_settings
from munipal.core.models.register import (
    RegisterDeal,
    RegisterDocument,
    RegisterFolder,
    RegisterReport,
)
from munipal.services.register_engine import build_package, digest, extract_document


class PrivateRegisterRoute(APIRoute):
    def get_route_handler(self):
        handler = super().get_route_handler()

        async def private(request):
            try:
                body = bytearray()
                async for part in request.stream():
                    body.extend(part)
                    if len(body) > 11_000_000:
                        raise HTTPException(413, "Request too large (10 MB file limit).")
                request._body = bytes(body)
                response = await handler(request)
                response.headers["Cache-Control"] = "no-store"
                response.headers["X-Content-Type-Options"] = "nosniff"
                return response
            except RequestValidationError:
                raise HTTPException(
                    422,
                    "Check the required fields and allowed values.",
                    headers={"Cache-Control": "no-store"},
                ) from None
            except HTTPException as exc:
                exc.headers = {**(exc.headers or {}), "Cache-Control": "no-store"}
                raise
            except Exception:
                raise HTTPException(
                    500,
                    "The register workspace is temporarily unavailable.",
                    headers={"Cache-Control": "no-store"},
                ) from None

        return private


router = APIRouter(route_class=PrivateRegisterRoute)


class DealCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    name: str = Field(min_length=2, max_length=200)
    legal_name: str = Field(min_length=2, max_length=255)
    professional_contact: str = Field(min_length=2, max_length=1000)
    bonds_already_closed: Literal[True]
    entity_type: Literal["private_obligated_person"]
    privacy_consent: Literal[True]


class Quote(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    amount_cents: int = Field(ge=50, le=10_000_000, strict=True)
    note: str = Field(min_length=3, max_length=4000)


class FolderCreate(BaseModel):
    url: str = Field(max_length=2000)

    @field_validator("url")
    @classmethod
    def cloud_link(cls, value):
        url = urlparse(value)
        host = (url.hostname or "").lower()
        if (
            url.scheme != "https"
            or url.username
            or url.password
            or url.port not in (None, 443)
            or not (
                host
                in {
                    "drive.google.com",
                    "dropbox.com",
                    "www.dropbox.com",
                    "1drv.ms",
                    "onedrive.live.com",
                    "app.box.com",
                }
                or host.endswith(".sharepoint.com")
                or host.endswith(".box.com")
            )
        ):
            raise ValueError(
                "Use a shared Google Drive, Dropbox, OneDrive, SharePoint or Box HTTPS link."
            )
        return value


class FolderUpdate(BaseModel):
    status: Literal["awaiting_import", "access_needed", "imported"]
    note: str = Field(min_length=1, max_length=2000)


def tenant(user):
    return (user.organization or "default").strip() or "default"


def operator_only(user):
    if not user.is_superuser:
        raise HTTPException(403, "Operator access required.")


async def owned_deal(db, user, deal_id, *, lock=False):
    statement = select(RegisterDeal).where(RegisterDeal.id == str(deal_id))
    if not user.is_superuser:
        statement = statement.where(
            RegisterDeal.owner_id == user.id, RegisterDeal.tenant_id == tenant(user)
        )
    if lock:
        statement = statement.with_for_update()
    deal = await db.scalar(statement)
    if not deal:
        raise HTTPException(404, "Not found")
    return deal


def paid(deal):
    if deal.payment_status != "paid":
        raise HTTPException(402, "Payment for this deal is required to build or download reports.")


def summary(deal):
    return {
        k: getattr(deal, k)
        for k in (
            "id",
            "name",
            "legal_name",
            "professional_contact",
            "payment_status",
            "amount_cents",
            "currency",
            "quote_note",
            "quote_version",
            "created_at",
        )
    }


def fields(row, keys):
    return {k: getattr(row, k) for k in keys.split()}


@router.get("/account")
async def account(user: StrictUser):
    return {"operator": user.is_superuser}


@router.get("/deals")
async def list_deals(user: StrictUser, db: DbSession, offset: int = Query(0, ge=0)):
    statement = select(RegisterDeal)
    if not user.is_superuser:
        statement = statement.where(
            RegisterDeal.owner_id == user.id, RegisterDeal.tenant_id == tenant(user)
        )
    deals = await db.scalars(
        statement.order_by(RegisterDeal.created_at.desc(), RegisterDeal.id).offset(offset).limit(50)
    )
    return [summary(d) for d in deals]


@router.post("/deals", status_code=201)
async def create_deal(payload: DealCreate, user: StrictUser, db: DbSession):
    deal = RegisterDeal(
        owner_id=user.id,
        tenant_id=tenant(user),
        name=payload.name,
        legal_name=payload.legal_name,
        professional_contact=payload.professional_contact,
    )
    db.add(deal)
    await db.commit()
    await db.refresh(deal)
    return summary(deal)


@router.get("/deals/{deal_id}")
async def detail(deal_id: UUID, user: StrictUser, db: DbSession):
    deal = await owned_deal(db, user, deal_id)
    result = summary(deal)
    documents = await db.scalars(
        select(RegisterDocument)
        .where(RegisterDocument.deal_id == deal.id)
        .order_by(RegisterDocument.created_at)
    )
    folders = await db.scalars(
        select(RegisterFolder)
        .where(RegisterFolder.deal_id == deal.id)
        .order_by(RegisterFolder.created_at)
    )
    reports = await db.scalars(
        select(RegisterReport)
        .where(RegisterReport.deal_id == deal.id)
        .order_by(RegisterReport.version.desc())
    )
    result.update(
        documents=[fields(d, "id filename sha256 size created_at") for d in documents],
        folders=[fields(f, "id url status note created_at") for f in folders],
        reports=[
            fields(r, "id version kind note candidate_count document_count sha256 created_at")
            for r in reports
        ],
    )
    return result


@router.post("/deals/{deal_id}/documents", status_code=201)
async def upload(deal_id: UUID, file: UploadFile, user: StrictUser, db: DbSession):
    deal = await owned_deal(db, user, deal_id, lock=True)
    content = await file.read(10_000_001)
    if not content or len(content) > 10_000_000:
        raise HTTPException(413, "Upload a nonempty file of at most 10 MB.")
    filename = re.sub(
        r"[^\w .()-]", "_", (file.filename or "document").replace("\\", "/").split("/")[-1]
    )[:200]
    sha = digest(content)
    existing = await db.scalar(
        select(RegisterDocument).where(
            RegisterDocument.deal_id == deal.id, RegisterDocument.sha256 == sha
        )
    )
    if existing:
        return fields(existing, "id filename sha256 size created_at")
    count, size = (
        await db.execute(
            select(func.count(), func.coalesce(func.sum(RegisterDocument.size), 0)).where(
                RegisterDocument.deal_id == deal.id
            )
        )
    ).one()
    if count >= 30 or size + len(content) > 50_000_000:
        raise HTTPException(
            409, "This deal has reached its 30-document or 50 MB intake limit. Contact the team."
        )
    try:
        extracted = await run_in_threadpool(extract_document, filename, content)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from None
    except Exception:
        raise HTTPException(
            422, "This file could not be read. Use an unencrypted, searchable document."
        ) from None
    doc = RegisterDocument(
        deal_id=deal.id,
        filename=filename,
        sha256=sha,
        size=len(content),
        content=content,
        extracted=extracted,
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)
    return fields(doc, "id filename sha256 size created_at")


@router.get("/deals/{deal_id}/documents/{document_id}")
async def download_document(deal_id: UUID, document_id: UUID, user: StrictUser, db: DbSession):
    deal = await owned_deal(db, user, deal_id)
    document = await db.scalar(
        select(RegisterDocument)
        .options(undefer(RegisterDocument.content))
        .where(RegisterDocument.id == str(document_id), RegisterDocument.deal_id == deal.id)
    )
    if not document:
        raise HTTPException(404, "Not found")
    return Response(
        document.content,
        media_type="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="source-{document.id}"'},
    )


@router.post("/deals/{deal_id}/folders", status_code=201)
async def attach_folder(deal_id: UUID, payload: FolderCreate, user: StrictUser, db: DbSession):
    deal = await owned_deal(db, user, deal_id, lock=True)
    count = await db.scalar(
        select(func.count()).select_from(RegisterFolder).where(RegisterFolder.deal_id == deal.id)
    )
    if count >= 10:
        raise HTTPException(409, "A deal can have at most ten shared folders.")
    folder = RegisterFolder(deal_id=deal.id, url=payload.url)
    db.add(folder)
    await db.commit()
    await db.refresh(folder)
    return fields(folder, "id url status note created_at")


@router.patch("/deals/{deal_id}/folders/{folder_id}")
async def update_folder(
    deal_id: UUID, folder_id: UUID, payload: FolderUpdate, user: StrictUser, db: DbSession
):
    operator_only(user)
    deal = await owned_deal(db, user, deal_id)
    folder = await db.scalar(
        select(RegisterFolder).where(
            RegisterFolder.id == str(folder_id), RegisterFolder.deal_id == deal.id
        )
    )
    if not folder:
        raise HTTPException(404, "Not found")
    folder.status, folder.note, folder.updated_by = payload.status, payload.note, user.id
    await db.commit()
    return fields(folder, "id url status note created_at")


@router.put("/deals/{deal_id}/quote")
async def quote(deal_id: UUID, payload: Quote, user: StrictUser, db: DbSession):
    operator_only(user)
    deal = await owned_deal(db, user, deal_id, lock=True)
    if deal.payment_status in {"paid", "refunded"} or deal.checkout_session_id:
        raise HTTPException(
            409, "The quote is locked after checkout starts. Let checkout expire before requoting."
        )
    if not await db.scalar(
        select(RegisterDocument.id).where(RegisterDocument.deal_id == deal.id).limit(1)
    ):
        raise HTTPException(409, "Import and review at least one source document before quoting.")
    deal.amount_cents, deal.quote_note = payload.amount_cents, payload.note
    deal.quote_version += 1
    deal.quoted_by, deal.payment_status = user.id, "awaiting_payment"
    await db.commit()
    return summary(deal)


@router.post("/deals/{deal_id}/checkout")
async def checkout(deal_id: UUID, user: StrictUser, db: DbSession):
    deal = await owned_deal(db, user, deal_id, lock=True)
    if deal.owner_id != user.id or deal.tenant_id != tenant(user):
        raise HTTPException(403, "Only the client can pay this quote.")
    if deal.payment_status != "awaiting_payment" or not deal.amount_cents:
        raise HTTPException(409, "A payable quote is required.")
    settings = get_settings()
    if not settings.stripe_secret_key or not settings.stripe_webhook_secret:
        raise HTTPException(503, "Online payments are not configured yet. Please contact the team.")
    try:
        if deal.checkout_session_id:
            session = await run_in_threadpool(
                stripe.checkout.Session.retrieve,
                deal.checkout_session_id,
                api_key=settings.stripe_secret_key,
            )
            if session.status == "expired":
                deal.checkout_session_id = None
                deal.checkout_url = None
                deal.quote_version += 1
                await db.commit()
                raise HTTPException(409, "Checkout expired. Please open checkout again.")
            if session.status != "open" or not session.url:
                raise HTTPException(409, "Payment is processing. Refresh this deal shortly.")
        else:
            metadata = {
                "register_deal_id": deal.id,
                "munipal_user_id": user.id,
                "register_quote_version": str(deal.quote_version),
            }
            session = await run_in_threadpool(
                stripe.checkout.Session.create,
                api_key=settings.stripe_secret_key,
                mode="payment",
                customer_email=user.email,
                line_items=[
                    {
                        "price_data": {
                            "currency": deal.currency,
                            "unit_amount": deal.amount_cents,
                            "product_data": {"name": "Muni-Pal Obligation Register — quoted deal"},
                        },
                        "quantity": 1,
                    }
                ],
                metadata=metadata,
                payment_intent_data={"metadata": metadata},
                success_url=f"{settings.register_frontend_url}/register/{deal.id}?checkout=success",
                cancel_url=f"{settings.register_frontend_url}/register/{deal.id}?checkout=cancel",
                idempotency_key=f"register-{deal.id}-{deal.quote_version}",
            )
            if not session.url:
                raise HTTPException(502, "Checkout is temporarily unavailable.")
            deal.checkout_session_id, deal.checkout_url = session.id, session.url
            await db.commit()
    except stripe.StripeError:
        raise HTTPException(
            502, "Checkout is temporarily unavailable. Try again shortly."
        ) from None
    return {"url": session.url}


@router.post("/deals/{deal_id}/build", status_code=201)
async def build(deal_id: UUID, user: StrictUser, db: DbSession):
    deal = await owned_deal(db, user, deal_id, lock=True)
    paid(deal)
    if deal.report_sequence >= 20:
        raise HTTPException(409, "This deal has reached 20 report versions. Contact the team.")
    documents = list(
        await db.scalars(
            select(RegisterDocument)
            .options(undefer(RegisterDocument.extracted))
            .where(RegisterDocument.deal_id == deal.id)
            .order_by(RegisterDocument.created_at, RegisterDocument.id)
        )
    )
    if not documents:
        raise HTTPException(409, "Upload source documents before building a candidate map.")
    if await db.scalar(
        select(RegisterFolder.id)
        .where(RegisterFolder.deal_id == deal.id, RegisterFolder.status != "imported")
        .limit(1)
    ):
        raise HTTPException(
            409, "The team must finish importing attached folders before building the package."
        )
    version = deal.report_sequence + 1
    content, count = await run_in_threadpool(
        build_package,
        deal.name,
        [fields(d, "id filename sha256 extracted") for d in documents],
        version,
    )
    report = RegisterReport(
        deal_id=deal.id,
        version=version,
        candidate_count=count,
        document_count=len(documents),
        content=content,
        sha256=digest(content),
    )
    deal.report_sequence = version
    db.add(report)
    await db.commit()
    await db.refresh(report)
    return fields(report, "id version kind note candidate_count document_count sha256 created_at")


@router.post("/deals/{deal_id}/deliveries", status_code=201)
async def publish_delivery(
    deal_id: UUID,
    file: UploadFile,
    user: StrictUser,
    db: DbSession,
    note: str = Form(min_length=3, max_length=4000),
):
    """Operators publish reviewed engine outputs, including approved registers."""
    operator_only(user)
    deal = await owned_deal(db, user, deal_id, lock=True)
    paid(deal)
    if deal.report_sequence >= 20:
        raise HTTPException(409, "This deal has reached 20 report versions.")
    content = await file.read(10_000_001)
    if len(content) > 10_000_000:
        raise HTTPException(413, "Delivery ZIP exceeds 10 MB.")
    try:
        with zipfile.ZipFile(io.BytesIO(content)) as archive:
            entries = archive.infolist()
            if not entries or len(entries) > 200 or sum(e.file_size for e in entries) > 50_000_000:
                raise ValueError()
            for entry in entries:
                path = PurePosixPath(entry.filename.replace("\\", "/"))
                if (
                    path.is_absolute()
                    or ".." in path.parts
                    or ":" in entry.filename
                    or entry.flag_bits & 1
                ):
                    raise ValueError()
    except (ValueError, zipfile.BadZipFile):
        raise HTTPException(
            422,
            "Use an unencrypted ZIP with safe relative filenames, at most 200 entries and 50 MB expanded.",
        ) from None
    report = RegisterReport(
        deal_id=deal.id,
        version=deal.report_sequence + 1,
        kind="team_delivery",
        note=note,
        published_by=user.id,
        candidate_count=0,
        document_count=0,
        content=content,
        sha256=digest(content),
    )
    deal.report_sequence += 1
    db.add(report)
    await db.commit()
    await db.refresh(report)
    return fields(report, "id version kind note candidate_count document_count sha256 created_at")


@router.get("/deals/{deal_id}/reports/{report_id}")
async def download_report(deal_id: UUID, report_id: UUID, user: StrictUser, db: DbSession):
    deal = await owned_deal(db, user, deal_id)
    paid(deal)
    report = await db.scalar(
        select(RegisterReport)
        .options(undefer(RegisterReport.content))
        .where(RegisterReport.id == str(report_id), RegisterReport.deal_id == deal.id)
    )
    if not report:
        raise HTTPException(404, "Not found")
    return Response(
        report.content,
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="obligation-package-v{report.version}.zip"'
        },
    )
