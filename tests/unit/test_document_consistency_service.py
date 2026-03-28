from munipal.core.schemas.deal_document import ConsistencyDomain, ConsistencySeverity
from munipal.services.document_consistency_service import DocumentConsistencyService


def test_extract_covenant_terms_from_text():
    text = """
    The minimum DSCR shall be 1.25x.
    Additional bonds test requires 1.35x coverage.
    Debt service reserve fund is set at 12 months.
    Cure period is 30 days after notice.
    """
    terms = DocumentConsistencyService._extract_terms(text, ConsistencyDomain.COVENANT)

    assert terms["dscr_min"] == 1.25
    assert terms["additional_bonds_test_dscr"] == 1.35
    assert terms["debt_service_reserve_months"] == 12.0
    assert terms["cure_period_days"] == 30.0


def test_compare_terms_detects_numeric_mismatch():
    issues, checked, matched = DocumentConsistencyService._compare_terms(
        domain=ConsistencyDomain.COVENANT,
        legal_terms={"dscr_min": 1.25, "debt_service_reserve_months": 12},
        model_terms={"dscr_min": 1.10, "debt_service_reserve_months": 12},
        tolerance_ratio=0.001,
        strict=False,
    )

    assert checked == 2
    assert matched == 1
    assert len(issues) == 1
    assert issues[0].field == "dscr_min"
    assert issues[0].severity == ConsistencySeverity.ERROR


def test_compare_terms_normalizes_percentage_ratios():
    issues, checked, matched = DocumentConsistencyService._compare_terms(
        domain=ConsistencyDomain.WATERFALL,
        legal_terms={"gp_carry_pct": 20},
        model_terms={"gp_carry_pct": 0.20},
        tolerance_ratio=0.0,
        strict=True,
    )

    assert checked == 1
    assert matched == 1
    assert issues == []
