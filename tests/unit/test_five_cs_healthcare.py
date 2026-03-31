"""Tests for healthcare-specific Five Cs credit assessment factors."""

import pytest

from munipal.engines.credit_analyzer.five_cs import (
    _score_collateral,
    _score_conditions,
    assess_five_cs,
)
from munipal.engines.credit_analyzer.models import ProjectInputs


# ---------------------------------------------------------------------------
# Conditions — healthcare risk flags
# ---------------------------------------------------------------------------

class TestConditionsHealthcareRiskFlags:
    """Conditions dimension should penalise healthcare-specific risks."""

    def _base_healthcare(self, **overrides) -> ProjectInputs:
        defaults = dict(
            project_name="Test Hospital",
            sector="healthcare",
            market_position="strong",
            sector_outlook="stable",
            regulatory_environment="stable",
            competitive_threats="moderate",
        )
        defaults.update(overrides)
        return ProjectInputs(**defaults)

    def test_reimbursement_rate_risk_penalises(self):
        without = self._base_healthcare(has_reimbursement_rate_risk=False)
        with_risk = self._base_healthcare(has_reimbursement_rate_risk=True)
        assert _score_conditions(with_risk).score < _score_conditions(without).score

    def test_payer_concentration_risk_penalises(self):
        without = self._base_healthcare(has_payer_concentration_risk=False)
        with_risk = self._base_healthcare(has_payer_concentration_risk=True)
        assert _score_conditions(with_risk).score < _score_conditions(without).score

    def test_certificate_of_need_risk_penalises(self):
        without = self._base_healthcare(has_certificate_of_need_risk=False)
        with_risk = self._base_healthcare(has_certificate_of_need_risk=True)
        assert _score_conditions(with_risk).score < _score_conditions(without).score

    def test_certificate_of_need_risk_in_risk_list(self):
        p = self._base_healthcare(has_certificate_of_need_risk=True)
        result = _score_conditions(p)
        assert any("certificate of need" in r.lower() for r in result.risks)

    def test_age_of_plant_penalises(self):
        young = self._base_healthcare(age_of_plant_years=5)
        old = self._base_healthcare(age_of_plant_years=20)
        assert _score_conditions(old).score < _score_conditions(young).score

    def test_age_of_plant_risk_message(self):
        p = self._base_healthcare(age_of_plant_years=25)
        result = _score_conditions(p)
        assert any("aging plant" in r.lower() for r in result.risks)

    def test_non_healthcare_ignores_healthcare_flags(self):
        """Healthcare risk flags should not affect non-healthcare sectors."""
        waste = ProjectInputs(
            project_name="Test WTE",
            sector="waste",
            market_position="strong",
            sector_outlook="stable",
            regulatory_environment="stable",
            competitive_threats="moderate",
            has_reimbursement_rate_risk=True,
            has_payer_concentration_risk=True,
            has_certificate_of_need_risk=True,
        )
        # These flags should not appear in risks for waste sector
        result = _score_conditions(waste)
        assert not any("reimbursement" in r.lower() for r in result.risks)
        assert not any("payer concentration" in r.lower() for r in result.risks)
        assert not any("certificate of need" in r.lower() for r in result.risks)


# ---------------------------------------------------------------------------
# Collateral — healthcare-specific factors
# ---------------------------------------------------------------------------

class TestCollateralHealthcareFactors:
    """Collateral dimension should score healthcare-specific factors."""

    def _base_healthcare(self, **overrides) -> ProjectInputs:
        defaults = dict(
            project_name="Test Hospital",
            sector="healthcare",
            pledge_type="net_revenue",
            lien_position="first",
        )
        defaults.update(overrides)
        return ProjectInputs(**defaults)

    def test_high_medicaid_concentration_penalises(self):
        low = self._base_healthcare(payer_mix_medicaid_pct=0.20)
        high = self._base_healthcare(payer_mix_medicaid_pct=0.70)
        assert _score_collateral(high).score < _score_collateral(low).score

    def test_high_medicaid_risk_message(self):
        p = self._base_healthcare(payer_mix_medicaid_pct=0.65)
        result = _score_collateral(p)
        assert any("medicaid" in r.lower() for r in result.risks)

    def test_favorable_commercial_payer_mix_bonus(self):
        commercial = self._base_healthcare(
            payer_mix_medicaid_pct=0.20,
            payer_mix_commercial_pct=0.60,
        )
        baseline = self._base_healthcare(payer_mix_medicaid_pct=0.20)
        assert _score_collateral(commercial).score >= _score_collateral(baseline).score

    def test_con_mitigant(self):
        p = self._base_healthcare(has_certificate_of_need=True)
        result = _score_collateral(p)
        assert any("certificate of need" in m.lower() for m in result.mitigants)

    def test_no_con_risk(self):
        p = self._base_healthcare(has_certificate_of_need=False)
        result = _score_collateral(p)
        assert any("con" in r.lower() for r in result.risks)

    def test_gross_patient_revenue_pledge(self):
        with_pledge = self._base_healthcare(patient_revenue_pledge="gross_patient")
        without = self._base_healthcare()
        assert _score_collateral(with_pledge).score > _score_collateral(without).score

    def test_net_patient_revenue_pledge(self):
        with_pledge = self._base_healthcare(patient_revenue_pledge="net_patient")
        without = self._base_healthcare()
        assert _score_collateral(with_pledge).score > _score_collateral(without).score

    def test_patient_revenue_pledge_finding(self):
        p = self._base_healthcare(patient_revenue_pledge="gross_patient")
        result = _score_collateral(p)
        assert any("patient revenue" in f.lower() for f in result.findings)


# ---------------------------------------------------------------------------
# Composite — healthcare project
# ---------------------------------------------------------------------------

class TestHealthcareComposite:
    """End-to-end assessment for a healthcare project."""

    def test_strong_healthcare_project(self):
        p = ProjectInputs(
            project_name="Strong Hospital Revenue Bonds",
            sector="healthcare",
            management=dict(
                team_experience_years=20,
                prior_projects_completed=5,
                prior_project_defaults=0,
                industry_expertise="deep",
                governance_structure="board_with_independents",
                regulatory_compliance_history="clean",
            ),
            historical_dscr=2.5,
            operating_margin=0.15,
            historical_revenue=100e6,
            revenue_growth_rate=0.05,
            total_assets=200e6,
            total_liabilities=60e6,
            total_equity=80e6,
            equity_contribution_pct=0.35,
            leverage_ratio=0.75,
            current_ratio=2.5,
            cash_on_hand=20e6,
            historical_expenses=80e6,
            pledge_type="gross_revenue",
            lien_position="first",
            has_insurance=True,
            credit_rating="A",
            market_position="strong",
            sector_outlook="growing",
            regulatory_environment="stable",
            competitive_threats="low",
            payer_mix_medicaid_pct=0.25,
            payer_mix_commercial_pct=0.55,
            has_certificate_of_need=True,
            patient_revenue_pledge="gross_patient",
        )
        result = assess_five_cs(p)
        assert result.composite_grade in ("A", "B")
        assert result.recommendation in ("strong_approve", "approve")

    def test_weak_healthcare_with_medicaid_risk(self):
        p = ProjectInputs(
            project_name="Weak Rural Hospital",
            sector="healthcare",
            historical_dscr=1.15,
            operating_margin=0.02,
            historical_revenue=10e6,
            pledge_type="net_revenue",
            lien_position="second",
            market_position="weak",
            sector_outlook="declining",
            regulatory_environment="challenging",
            competitive_threats="high",
            payer_mix_medicaid_pct=0.75,
            has_reimbursement_rate_risk=True,
            has_payer_concentration_risk=True,
            has_certificate_of_need_risk=True,
            age_of_plant_years=30,
        )
        result = assess_five_cs(p)
        assert result.composite_grade in ("C", "D", "F")
        assert len(result.key_risks) > 0
