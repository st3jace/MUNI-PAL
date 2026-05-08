"""Unit tests for advisory package risk integration enrichment."""

from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import UUID

import pytest

from munipal.services.advisory_package_service import ExternalPackageService, InternalReportService


class _FactStub:
    def __init__(self, value):
        self.value = value


class _ProjectStub:
    def __init__(
        self,
        *,
        name: str | None = None,
        description: str | None = None,
        issuer_name: str | None = None,
        project_location: str | None = None,
        target_bond_amount: float | None = None,
    ) -> None:
        self.name = name
        self.description = description
        self.issuer_name = issuer_name
        self.project_location = project_location
        self.target_bond_amount = target_bond_amount


class _PackageStub:
    def __init__(
        self,
        *,
        disclosure_completeness_score: float | None = 0.9,
        critical_tbd_count: int = 0,
        disclaimer: str = "present",
        deal_overview: dict | None = None,
    ) -> None:
        self.disclosure_completeness_score = disclosure_completeness_score
        self.critical_tbd_count = critical_tbd_count
        self.disclaimer = disclaimer
        self.deal_overview = deal_overview or {"project_summary": "ok"}


def _service() -> ExternalPackageService:
    return ExternalPackageService(session=None)  # type: ignore[arg-type]


def test_external_executive_summary_includes_risk_context_metrics() -> None:
    service = _service()
    summary = service._build_executive_summary(  # noqa: SLF001
        facts={
            "capital.project-cost": _FactStub(125000000),
            "finmodel.outputs.dscrbase": _FactStub(1.42),
        },
        risk_context={
            "integration_mode": "full",
            "overall_posture_score": 0.812,
            "directional_guidance_only": False,
            "fallback_reasons": [],
        },
    )

    key_metrics = summary["key_metrics"]
    assert key_metrics["Risk Integration Mode"] == "Full"
    assert key_metrics["Risk Posture Score"] == "0.812"
    assert key_metrics["Risk Guidance"] == "Review Ready"
    assert "advisor review support" in summary["next_steps"].lower()


def test_external_executive_summary_flags_fallback_mode() -> None:
    service = _service()
    summary = service._build_executive_summary(  # noqa: SLF001
        facts={},
        risk_context={
            "integration_mode": "fallback",
            "overall_posture_score": 0.331,
            "directional_guidance_only": True,
            "fallback_reasons": ["One or more risk dimensions are low reliability."],
        },
    )

    assert summary["key_metrics"]["Risk Guidance"] == "Directional"
    assert "fallback mode" in summary["next_steps"].lower()
    assert "low reliability" in summary["next_steps"].lower()


def test_external_key_assumptions_include_risk_analytics_entries() -> None:
    service = _service()
    assumptions = service._build_key_assumptions(  # noqa: SLF001
        facts={},
        risk_context={
            "integration_mode": "fallback",
            "overall_posture_score": 0.412,
            "directional_guidance_only": True,
            "fallback_reasons": ["Directional guidance due to low reliability."],
            "top_next_steps": ["Strengthen DSCR covenant package."],
        },
    )

    risk_assumptions = [item for item in assumptions if item["category"] == "Risk Analytics"]
    assert len(risk_assumptions) >= 2
    assert any(item["assumption"] == "BFMS Integration Mode" for item in risk_assumptions)
    assert any(item["assumption"] == "Fallback Rationale" for item in risk_assumptions)
    assert any(item["assumption"] == "Priority Risk Action" for item in risk_assumptions)


def test_infer_risk_cohort_values_for_healthcare_conduit_profile() -> None:
    service = _service()
    cohort = service._infer_risk_benchmark_cohort_values(  # noqa: SLF001
        project=None,
        facts={
            "project.canonicaldescription": _FactStub(
                "Community health clinic modernization and patient care expansion."
            ),
            "parties.issuer.name": _FactStub(
                "Industrial Development Authority of the City of Sierra Vista"
            ),
            "parties.borrower.name": _FactStub("Chiricahua Community Health Centers, Inc."),
            "cab.originalprincipial": _FactStub(250000),
        },
    )

    assert cohort["sector"] == "healthcare"
    assert cohort["deal_type"] == "conduit"
    assert cohort["issuer_size_band"] == "small"
    assert cohort["sample_size"] == 24


def test_infer_risk_cohort_values_fallback_to_project_metadata() -> None:
    service = _service()
    cohort = service._infer_risk_benchmark_cohort_values(  # noqa: SLF001
        project=_ProjectStub(
            name="Regional Hospital Campus Improvements",
            description="Healthcare infrastructure expansion project.",
            issuer_name="County Health Facilities Authority",
            project_location="AZ",
            target_bond_amount=120_000_000,
        ),
        facts={},
    )

    assert cohort["sector"] == "healthcare"
    assert cohort["deal_type"] == "revenue"
    assert cohort["issuer_size_band"] == "mid"
    assert cohort["sample_size"] == 30


def test_distribution_validation_blocks_unresolved_critical_conflicts() -> None:
    service = _service()
    package = _PackageStub()

    validation = service._validate_for_distribution(  # noqa: SLF001
        package,  # type: ignore[arg-type]
        critical_conflict_count=2,
        material_conflict_count=1,
        unresolved_conflict_count=3,
    )

    assert validation.ready_for_distribution is False
    assert any("Unresolved critical fact conflicts" in issue for issue in validation.issues)


def test_distribution_validation_keeps_material_conflicts_as_warning_only() -> None:
    service = _service()
    package = _PackageStub()

    validation = service._validate_for_distribution(  # noqa: SLF001
        package,  # type: ignore[arg-type]
        critical_conflict_count=0,
        material_conflict_count=2,
        unresolved_conflict_count=2,
    )

    assert validation.ready_for_distribution is True
    assert validation.issues == []
    assert any("Unresolved material fact conflicts" in warning for warning in validation.warnings)


@pytest.mark.asyncio
async def test_internal_evidence_index_exposes_canonical_and_ledger_views(monkeypatch) -> None:
    service = InternalReportService(session=None)  # type: ignore[arg-type]
    now = datetime.now(UTC)

    class _ConflictDetectorStub:
        async def find_conflicts(self, _project_id):
            return [{
                "schema_path": "capital.project-cost",
                "criticality": "critical",
                "fact_count": 2,
                "unique_value_count": 2,
            }]

    monkeypatch.setattr(
        "munipal.services.advisory_package_service.FactConflictDetector",
        lambda _session: _ConflictDetectorStub(),
    )

    facts = [
        SimpleNamespace(
            id="f-1",
            schema_path="capital.project-cost",
            value=40000000,
            confidence_score=0.98,
            review_status="approved",
            criticality="critical",
            source_type="extracted",
            lifecycle_state="active",
            duplicate_classification="unique",
            is_canonical=True,
            canonical_score=0.95,
            created_at=now,
            updated_at=now,
        ),
        SimpleNamespace(
            id="f-2",
            schema_path="capital.project-cost",
            value=45000000,
            confidence_score=0.90,
            review_status="approved",
            criticality="critical",
            source_type="extracted",
            lifecycle_state="active",
            duplicate_classification="candidate_conflict",
            is_canonical=False,
            canonical_score=0.70,
            created_at=now,
            updated_at=now,
        ),
    ]

    evidence = await service._build_evidence_index(  # noqa: SLF001
        UUID("00000000-0000-0000-0000-000000000001"),
        facts,  # type: ignore[arg-type]
    )

    assert evidence["summary"]["canonical_total"] == 1
    assert "capital" in evidence["canonical_by_domain"]
    assert "capital" in evidence["ledger_by_domain"]
    assert evidence["conflict_summary"]["critical"] == 1


def test_external_package_language_stays_advisor_review_safe() -> None:
    service = _service()
    summary = service._build_executive_summary(  # noqa: SLF001
        facts={
            "parties.issuer.name": _FactStub("County Health Facilities Authority"),
            "project.canonicaldescription": _FactStub("hospital campus modernization"),
            "cab.originalprincipial": _FactStub(25000000),
        },
        risk_context={
            "integration_mode": "full",
            "overall_posture_score": 0.812,
            "directional_guidance_only": False,
            "fallback_reasons": [],
        },
    )
    overview = service._build_deal_overview({})  # noqa: SLF001
    rendered = "\n".join([
        str(summary),
        str(overview),
    ]).lower()

    prohibited = (
        "execution-grade advisory decisioning",
        "stable for advisory decisioning",
        "proposes to issue",
        "proposed bond amount",
        "issuance_intent': 'revenue bond financing",
    )
    for phrase in prohibited:
        assert phrase not in rendered

    assert "registered advisor" in rendered or "registered municipal advisor" in rendered
    assert "review" in rendered
