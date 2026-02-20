"""Unit tests for advisory package risk integration enrichment."""

from munipal.services.advisory_package_service import ExternalPackageService


class _FactStub:
    def __init__(self, value):
        self.value = value


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
    assert key_metrics["Risk Guidance"] == "Execution Grade"
    assert "full mode" in summary["next_steps"].lower()


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
