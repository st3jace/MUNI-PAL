"""Tests for BFMS issuer-side deal workflow punchlist contracts."""

from datetime import date

import pytest

from munipal.services.deal_workflow import (
    DealWorkflowValidationError,
    OpenItemStatus,
    build_deal_workflow_from_seed,
    build_deal_workflow_rollup,
    initialize_deal_workflow_from_pilot,
    validate_deal_workflow,
)
from munipal.services.pilot_onboarding import build_pilot_onboarding_workflow


def test_deal_workflow_schema_validates_reference_fixture_and_issuer_first_rollup() -> None:
    workflow = validate_deal_workflow(
        {
            "deal": {
                "id": "ala-johnston-2026",
                "name": "ALA Johnston",
                "year": 2026,
                "series_label": "Series 2026",
                "conduit_issuer": "SVIDA",
                "borrower": "American Leadership Academy - Johnston",
                "type": "Charter School Revenue Bonds",
                "phase": "pre-closing",
                "closing_date": "2026-04-29",
            },
            "working_group": [
                {"counterparty": "SVIDA", "role": "Conduit Issuer", "lead": "Stephen Peterson", "lead_email": "issuer@example.test", "is_owner_bucket": True, "is_self": True},
                {"counterparty": "Ice Miller", "role": "Bond Counsel", "lead": "Brian Magorien", "lead_email": "counsel@example.test", "is_owner_bucket": True, "is_self": False},
            ],
            "documents": [
                {"id": "closing-memo", "name": "Closing Memo", "owner": "Ice Miller", "current_state": "rev_1", "states_completed": ["not_started", "rev_1"], "category": "closing", "required": True}
            ],
            "open_items": [
                {"id": "issuer-sig-pages", "owner": "SVIDA", "description": "Return issuer signature pages.", "status": "pending", "blocks_closing": True, "source": {"system": "counsel_email", "message_id": "msg-1", "audit_date": "2026-04-24"}, "related_documents": ["closing-memo"]},
                {"id": "counsel-redlines", "owner": "Ice Miller", "description": "Circulate final redlines.", "status": "in_progress", "blocks_closing": False, "source": {"system": "counsel_email", "message_id": "msg-1", "audit_date": "2026-04-24"}, "related_documents": ["closing-memo"]},
            ],
            "forward_commitments": [],
            "phase_timeline": [{"phase": "pre-closing", "target_date": "2026-04-29", "status": "current"}],
            "snapshots": [],
            "metadata": {"human_confirmation_required": True, "liability_boundary": "mirror_only"},
        }
    )

    assert workflow.deal.id == "ala-johnston-2026"
    assert workflow.self_owner_counterparties == ("SVIDA",)
    assert [item.id for item in workflow.issuer_first_open_items()] == ["issuer-sig-pages", "counsel-redlines"]
    assert workflow.blocking_open_items()[0].id == "issuer-sig-pages"


def test_deal_workflow_validation_rejects_unknown_references_and_unsafe_boundary() -> None:
    workflow = build_deal_workflow_from_seed(deal_id="oakport-healthcare-2026", name="Oakport Healthcare", year=2026, borrower="Oakport Regional Medical Center", conduit_issuer="SVIDA", sector="healthcare", bond_counsel="Ice Miller LLP", underwriter="Baird", closing_date=date(2026, 8, 15))
    workflow.open_items[0].owner = "Unknown Owner"

    with pytest.raises(DealWorkflowValidationError, match="unknown owner"):
        validate_deal_workflow(workflow)

    workflow = build_deal_workflow_from_seed(deal_id="oakport-healthcare-2026", name="Oakport Healthcare", year=2026, borrower="Oakport Regional Medical Center", conduit_issuer="SVIDA", sector="healthcare")
    workflow.metadata.liability_boundary = "approval"
    with pytest.raises(DealWorkflowValidationError, match="mirror-only"):
        validate_deal_workflow(workflow)


def test_create_deal_workflow_from_seed_initializes_standard_parties_documents_and_timeline() -> None:
    workflow = build_deal_workflow_from_seed(
        deal_id="oakport-healthcare-2026", name="Oakport Healthcare", year=2026, borrower="Oakport Regional Medical Center", conduit_issuer="SVIDA", sector="healthcare", bond_counsel="Ice Miller LLP", issuer_counsel="Slania Law", borrower_counsel="Quarles and Brady LLP", municipal_advisor="Partner Capital Advisors", underwriter="Baird", trustee="UMB Bank", title_company="FNF Title", target_closing_date=date(2026, 8, 15), pricing_date=date(2026, 8, 8), series_label="Series 2026A", par_amount_usd=25000000, primary_counsel_email_pattern="*@icemiller.com", additional_document_templates=("healthcare-operating-statement",)
    )

    roles = {party.role for party in workflow.working_group}
    assert {"Conduit Issuer", "Bond Counsel", "Issuer Counsel", "Borrower Counsel", "Financial Advisor", "Underwriter", "Trustee", "Title Company", "Borrower"} <= roles
    assert workflow.working_group[0].counterparty == "SVIDA"
    assert workflow.working_group[0].is_self is True
    assert {doc.id for doc in workflow.documents} >= {"closing-memo", "bond-purchase-agreement", "healthcare-operating-statement"}
    assert any(step.phase == "pricing" and step.target_date == date(2026, 8, 8) for step in workflow.phase_timeline)
    assert workflow.metadata.primary_counsel_email_pattern == "*@icemiller.com"


def test_pilot_onboarding_can_optionally_initialize_workflow_and_link_readiness_gaps() -> None:
    pilot = build_pilot_onboarding_workflow("healthcare", sensing_lead_id="lead-123", source_channel="readiness_scan")

    workflow = initialize_deal_workflow_from_pilot(
        pilot, deal_id="oakport-healthcare-2026", borrower="Oakport Regional Medical Center", conduit_issuer="SVIDA", advisor="Registered MA LLC", reviewer="Bond Strategist", target_closing_date=date(2026, 8, 15), readiness_gap_refs=("gap:audited-financials", "gap:days-cash-on-hand"), handoff_output_refs=("handoff_pack", "evidence_index")
    )

    assert workflow.metadata.pilot_workflow_id == pilot.workflow_id
    assert workflow.metadata.deal_workflow_tracking_enabled is True
    assert "pilot_workflow_snapshots" in workflow.metadata.measurement_hooks
    assert "no_approval_no_sizing_no_pricing_advice" in workflow.metadata.liability_disclaimers
    assert [item.related_handoff_outputs for item in workflow.open_items if item.id.startswith("readiness-gap-")]
    assert {item.status for item in workflow.open_items} == {OpenItemStatus.PENDING}


def test_rollup_returns_self_owned_items_blockers_stale_items_and_human_confirmation_label() -> None:
    active = build_deal_workflow_from_seed(deal_id="oakport-healthcare-2026", name="Oakport Healthcare", year=2026, borrower="Oakport Regional Medical Center", conduit_issuer="SVIDA", sector="healthcare", target_closing_date=date(2026, 8, 15))
    active.open_items[0].last_updated = date(2026, 7, 1)
    active.open_items[0].blocks_closing = True
    active.open_items[0].owner = "SVIDA"

    other = build_deal_workflow_from_seed(deal_id="harbor-housing-2026", name="Harbor Housing", year=2026, borrower="Harbor Affordable Housing LP", conduit_issuer="SVIDA", sector="housing", target_closing_date=date(2026, 9, 1))

    rollup = build_deal_workflow_rollup([active, other], as_of=date(2026, 7, 20), stale_after_days=10)

    assert rollup.human_confirmation_required is True
    assert rollup.active_deal_count == 2
    assert rollup.blocking_item_count == 1
    assert rollup.self_owned_open_items[0].deal_id == "oakport-healthcare-2026"
    assert rollup.stale_items[0].item_id == active.open_items[0].id
    assert rollup.upcoming_closings[0].deal_id == "oakport-healthcare-2026"


def test_parse_counsel_email_extracts_owner_grouped_items_statuses_and_commitments() -> None:
    from munipal.services.deal_workflow import parse_counsel_punchlist_email

    parsed = parse_counsel_punchlist_email(
        subject="ALA Johnston - updated open items and LOM proof",
        body="""
        Brian Magorien sent the following open items we are tracking for closing:

        SVIDA/Authority Open Items:
        - Return issuer signature pages - pending (Stephen Peterson)
        - Confirm wire instructions - awaiting response (Michael Slania)

        Ice Miller Open Items:
        - LOM proof circulated for signature - circulated for signature (Brian Magorien)

        In preparation for closing, we expect to complete the following:
        - Open pre-closing file on Monday
        - Circulate final closing memorandum
        """,
        source_author="Brian Magorien",
        audit_date=date(2026, 4, 24),
        message_id="ice-2026-04-24",
    )

    assert parsed.private_body_redacted is True
    assert [item.inferred_owner for item in parsed.open_items] == ["SVIDA", "SVIDA", "Ice Miller"]
    assert [item.status for item in parsed.open_items] == [
        OpenItemStatus.PENDING,
        OpenItemStatus.AWAITING_RESPONSE,
        OpenItemStatus.CIRCULATED_FOR_SIGNATURE,
    ]
    assert parsed.open_items[0].description == "Return issuer signature pages"
    assert parsed.open_items[0].status_verb == "pending"
    assert parsed.open_items[0].owner_individual == "Stephen Peterson"
    assert parsed.open_items[0].audit_breadcrumb.message_id == "ice-2026-04-24"
    assert [commitment.description for commitment in parsed.forward_commitments] == [
        "Open pre-closing file on Monday",
        "Circulate final closing memorandum",
    ]


def test_parse_counsel_email_handles_slight_counsel_variation_and_document_signals() -> None:
    from munipal.services.deal_workflow import parse_counsel_punchlist_email

    parsed = parse_counsel_punchlist_email(
        subject="Re: ALA Johnston Closing Memo executed and filed",
        body="""
        Updated short list of the open items:
        * Authority: Confirm resolution certificate - outstanding (Stephen Peterson)
        * Trustee: UMB to release authentication receipt - received (Katie Carlson)
        * Borrower Counsel: Title endorsement is blocked (Monika Calamita)
        Thanks,
        Counsel Team
        """,
        source_author="Martha Martinez Karasch",
        audit_date=date(2026, 4, 25),
        message_id="pca-2026-04-25",
    )

    assert [item.inferred_owner for item in parsed.open_items] == ["SVIDA", "UMB Bank", "Borrower Counsel"]
    assert [item.status for item in parsed.open_items] == [
        OpenItemStatus.PENDING,
        OpenItemStatus.COMPLETED,
        OpenItemStatus.BLOCKED,
    ]
    assert parsed.document_signals[0].document_id == "closing-memo"
    assert parsed.document_signals[0].next_state == "filed"
    assert parsed.document_signals[0].confidence >= 0.75


def test_refresh_diff_adds_updates_conservatively_closes_and_advances_documents() -> None:
    from munipal.services.deal_workflow import apply_counsel_refresh, parse_counsel_punchlist_email

    workflow = build_deal_workflow_from_seed(
        deal_id="ala-johnston-2026",
        name="ALA Johnston",
        year=2026,
        borrower="American Leadership Academy - Johnston",
        conduit_issuer="SVIDA",
        sector="education",
        bond_counsel="Ice Miller",
        trustee="UMB Bank",
        target_closing_date=date(2026, 4, 29),
    )
    workflow.open_items[0].id = "svida-signature-pages"
    workflow.open_items[0].description = "Return issuer signature pages"
    workflow.open_items[0].owner = "SVIDA"
    workflow.open_items[0].status = OpenItemStatus.PENDING
    workflow.open_items[0].source.source_author = "Brian Magorien"
    workflow.open_items[0].source.audit_date = date(2026, 4, 24)
    workflow.open_items.append(
        workflow.open_items[0].model_copy(
            deep=True,
            update={
                "id": "stale-issuer-certificate",
                "description": "Confirm issuer certificate",
                "status": OpenItemStatus.PENDING,
                "source": workflow.open_items[0].source.model_copy(deep=True),
            },
        )
    )

    parsed = parse_counsel_punchlist_email(
        subject="ALA Johnston Closing Memo executed and filed",
        body="""
        Open items we are tracking for closing:
        SVIDA/Authority Open Items:
        - Return issuer signature pages - received (Stephen Peterson)
        UMB Bank Open Items:
        - Release authentication receipt - awaiting response (Katie Carlson)
        """,
        source_author="Brian Magorien",
        audit_date=date(2026, 4, 25),
        message_id="ice-2026-04-25",
    )

    diff = apply_counsel_refresh(workflow, parsed)

    assert diff.added_item_ids == ("counsel-umb-bank-release-authentication-receipt",)
    assert diff.updated_item_ids == ("svida-signature-pages",)
    assert diff.closed_item_ids == ("stale-issuer-certificate",)
    assert diff.document_state_changes == ("closing-memo:filed",)
    refreshed = diff.refreshed_workflow
    assert refreshed.open_items_by_id["svida-signature-pages"].status == OpenItemStatus.COMPLETED
    assert refreshed.open_items_by_id["svida-signature-pages"].completed_date == date(2026, 4, 25)
    assert refreshed.open_items_by_id["stale-issuer-certificate"].status == OpenItemStatus.COMPLETED
    assert refreshed.open_items_by_id["stale-issuer-certificate"].human_confirmation_required is True
    assert refreshed.document_state_matrix()["closing-memo"] == "filed"
    assert refreshed.snapshots[-1].source.message_id == "ice-2026-04-25"


def test_refresh_diff_does_not_close_missing_items_from_different_author_or_older_email() -> None:
    from munipal.services.deal_workflow import apply_counsel_refresh, parse_counsel_punchlist_email

    workflow = build_deal_workflow_from_seed(
        deal_id="ala-johnston-2026",
        name="ALA Johnston",
        year=2026,
        borrower="American Leadership Academy - Johnston",
        conduit_issuer="SVIDA",
        sector="education",
        bond_counsel="Ice Miller",
    )
    workflow.open_items[0].source.source_author = "Brian Magorien"
    workflow.open_items[0].source.audit_date = date(2026, 4, 25)

    parsed = parse_counsel_punchlist_email(
        subject="ALA Johnston - older update",
        body="""
        Open items we are tracking for closing:
        Ice Miller Open Items:
        - Circulate LOM proof - in progress (Brian Magorien)
        """,
        source_author="Different Counsel",
        audit_date=date(2026, 4, 24),
        message_id="older-different-author",
    )

    diff = apply_counsel_refresh(workflow, parsed)

    assert diff.closed_item_ids == ()
    assert workflow.open_items[0].status == OpenItemStatus.PENDING
