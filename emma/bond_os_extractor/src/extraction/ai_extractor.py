from __future__ import annotations

import json
import logging
import re
from typing import Any

from tenacity import retry, stop_after_attempt, wait_exponential

from ..config import get_settings
from .base_extractor import BaseExtractor, ExtractionTier
from .cache import compute_cache_key, load_from_cache, save_to_cache

logger = logging.getLogger("bond_os_extractor.extraction.ai")

SYSTEM_PROMPT = """You are a municipal bond analyst extracting structured data from Official Statement text.

CRITICAL RULES:
- Extract ONLY what is explicitly stated in the text.
- If a field is not present in the text, return null.
- Never infer, estimate, or hallucinate values.
- A null extraction is always preferable to a guessed one.
- Return valid JSON only, no markdown or commentary.

For each field, also provide a confidence score (0.0-1.0) in a parallel "_confidence" object."""


class AnthropicClient:
    """Standalone Anthropic client for bond extraction."""

    def __init__(self) -> None:
        settings = get_settings()
        self.api_key = settings.anthropic_api_key
        self.model = settings.anthropic_model
        self.max_tokens = settings.anthropic_max_tokens
        self._client: Any = None

    def _get_client(self) -> Any:
        if self._client is None:
            import anthropic
            self._client = anthropic.Anthropic(api_key=self.api_key)
        return self._client

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
    )
    def extract(self, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        client = self._get_client()
        response = client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=0.0,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        text = response.content[0].text
        return _parse_json_response(text)


def _parse_json_response(text: str) -> dict[str, Any]:
    """Parse JSON from an AI response, handling common formatting issues.

    Tries multiple strategies:
    1. Direct json.loads after stripping markdown fences
    2. Extract the first {...} block from the text
    """
    text = text.strip()

    # Strip markdown code fences
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
        text = text.strip()

    # Strategy 1: direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Strategy 2: find the first {...} block (AI sometimes adds commentary)
    brace_start = text.find("{")
    if brace_start >= 0:
        depth = 0
        for i in range(brace_start, len(text)):
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
                if depth == 0:
                    candidate = text[brace_start : i + 1]
                    try:
                        return json.loads(candidate)
                    except json.JSONDecodeError:
                        break

    logger.warning("Could not parse JSON from AI response (%d chars)", len(text))
    raise json.JSONDecodeError("No valid JSON found in AI response", text[:200], 0)


# ---------------------------------------------------------------------------
# AI Extractors
# ---------------------------------------------------------------------------

class DealIdentityAIExtractor(BaseExtractor):
    tier = ExtractionTier.TIER_2
    name = "ai_deal_identity"

    def __init__(self, client: AnthropicClient | None = None) -> None:
        self.client = client or AnthropicClient()

    def extract(self, section_text: str, section_id: str, tables=None) -> dict[str, Any]:
        prompt = f"""Extract the deal identity from this Official Statement section titled "{section_id}":

{section_text[:8000]}

Return a JSON object with these exact fields:
{{
  "issuer_name": "legal name of the issuer or null",
  "issuer_type": "state|county|city|town|village|special_district|authority|ida|school_district|utility|housing|health or null",
  "issuer_state": "two-letter state code or null",
  "issuer_county": "county name or null",
  "borrower_name": "conduit borrower name or null",
  "borrower_type": "type of borrower or null",
  "trustee_name": "trustee name or null",
  "bond_counsel": "bond counsel firm or null",
  "underwriter_names": ["list of underwriter names"],
  "underwriter_counsel": "underwriter's counsel or null",
  "municipal_advisor": "municipal advisor name or null",
  "disclosure_counsel": "disclosure counsel or null",
  "paying_agent": "paying agent or null",
  "registrar": "registrar or null",
  "verification_agent": "verification agent or null",
  "official_title": "full bond title from cover or null",
  "_confidence": {{field_name: 0.0-1.0 for each field}}
}}"""
        return self.client.extract(SYSTEM_PROMPT, prompt)


class SecurityAIExtractor(BaseExtractor):
    tier = ExtractionTier.TIER_2
    name = "ai_security"

    def __init__(self, client: AnthropicClient | None = None) -> None:
        self.client = client or AnthropicClient()

    def extract(self, section_text: str, section_id: str, tables=None) -> dict[str, Any]:
        prompt = f"""Extract the security package from this Official Statement section titled "{section_id}":

{section_text[:8000]}

Return a JSON object with these exact fields:
{{
  "pledge_type": "gross_revenue|net_revenue|specific_revenue|none or null",
  "pledged_revenues_description": "description or null",
  "lien_position": "first|second|pari_passu|subordinate or null",
  "senior_debt_outstanding": number or null,
  "real_property_mortgage": true/false,
  "equipment_security_interest": true/false,
  "offtake_agreements_assigned": true/false,
  "offtake_counterparties": ["list"] or [],
  "rate_covenant": {{
    "covenant_type": "rate|coverage|rate_and_coverage or null",
    "minimum_coverage_ratio": number or null,
    "coverage_calculation_basis": "description or null",
    "consultant_rate_study_required": true/false,
    "cure_period_days": number or null
  }} or null,
  "additional_bonds_test": {{
    "historical_coverage_required": number or null,
    "projected_coverage_required": number or null,
    "lookback_period_years": number or null,
    "consultant_certification_required": true/false
  }} or null,
  "debt_service_reserve_fund": {{
    "requirement_type": "maximum_annual_debt_service|average_annual_debt_service|percent_of_par|fixed_amount|lesser_of_three_prong or null",
    "amount": number or null,
    "funded_at_closing": true/false,
    "surety_bond_permitted": true/false
  }} or null,
  "_confidence": {{field_name: 0.0-1.0 for each field}}
}}"""
        return self.client.extract(SYSTEM_PROMPT, prompt)


class DealStructureAIExtractor(BaseExtractor):
    tier = ExtractionTier.TIER_2
    name = "ai_deal_structure"

    def __init__(self, client: AnthropicClient | None = None) -> None:
        self.client = client or AnthropicClient()

    def extract(self, section_text: str, section_id: str, tables=None) -> dict[str, Any]:
        prompt = f"""Extract the deal structure from this Official Statement section titled "{section_id}":

{section_text[:8000]}

Return a JSON object with these exact fields:
{{
  "bond_type": "general_obligation|revenue|conduit_revenue|special_assessment|tax_increment|moral_obligation|double_barrel|lease_revenue|certificates_of_participation|industrial_development|private_activity|qualified_501c3 or null",
  "tax_status": "tax_exempt|taxable|alternative_minimum_tax|bank_qualified|federally_taxable_state_exempt or null",
  "interest_type": "fixed_rate|variable_rate|capital_appreciation|convertible_cab|zero_coupon|stepped_coupon|index_linked|auction_rate or null",
  "denomination": number or null,
  "cab_enabled": true/false,
  "cab_accretion_rate": number or null,
  "cab_conversion_date": "YYYY-MM-DD or null",
  "slb_enabled": true/false,
  "green_bond": true/false,
  "social_bond": true/false,
  "sustainability_bond": true/false,
  "maturity_type": "serial|term|serial_and_term|bullet|capital_appreciation|convertible or null",
  "final_maturity_date": "YYYY-MM-DD or null",
  "optional_redemption_date": "YYYY-MM-DD or null",
  "optional_redemption_price": number or null,
  "make_whole_call": true/false,
  "extraordinary_redemption": true/false,
  "mandatory_sinking_fund": true/false,
  "turbo_redemption": true/false,
  "credit_enhancement_type": "none|bond_insurance|letter_of_credit|standby_purchase_agreement|state_enhancement|moral_obligation|federal_guarantee or null",
  "credit_enhancer_name": "name or null",
  "_confidence": {{field_name: 0.0-1.0 for each field}}
}}"""
        return self.client.extract(SYSTEM_PROMPT, prompt)


class RiskFactorsAIExtractor(BaseExtractor):
    tier = ExtractionTier.TIER_2
    name = "ai_risk_factors"

    def __init__(self, client: AnthropicClient | None = None) -> None:
        self.client = client or AnthropicClient()

    def extract(self, section_text: str, section_id: str, tables=None) -> dict[str, Any]:
        prompt = f"""Extract and classify risk factors from this Official Statement section titled "{section_id}":

{section_text[:12000]}

Return a JSON object with these exact fields:
{{
  "risks": [
    {{
      "category": "construction|technology|market_demand|regulatory|environmental|competition|management|financial|interest_rate|tax_law|force_majeure|political|feedstock_supply|offtake_counterparty|permitting|litigation|labor|insurance|cybersecurity|climate|pandemic",
      "title": "short risk title",
      "description": "1-2 sentence summary",
      "severity_implied": "boilerplate|material|significant",
      "mitigation_described": true/false,
      "mitigation_text": "mitigation summary or null"
    }}
  ],
  "total_risk_factors_count": number,
  "has_project_specific_risks": true/false,
  "has_technology_risk": true/false,
  "has_construction_risk": true/false,
  "has_environmental_compliance_risk": true/false,
  "_confidence": {{"risks": 0.0-1.0}}
}}"""
        return self.client.extract(SYSTEM_PROMPT, prompt)


class FlowOfFundsAIExtractor(BaseExtractor):
    tier = ExtractionTier.TIER_2
    name = "ai_flow_of_funds"

    def __init__(self, client: AnthropicClient | None = None) -> None:
        self.client = client or AnthropicClient()

    def extract(self, section_text: str, section_id: str, tables=None) -> dict[str, Any]:
        prompt = f"""Extract the flow of funds / cash waterfall from this Official Statement section titled "{section_id}":

{section_text[:8000]}

Return a JSON object with these exact fields:
{{
  "waterfall_steps": [
    {{
      "priority": 1,
      "fund_name": "fund name",
      "description": "what goes into this fund",
      "amount_or_formula": "e.g. 1/12 of annual debt service"
    }}
  ],
  "trapped_cash_provisions": true/false,
  "sweep_to_equity_permitted": true/false,
  "_confidence": {{"waterfall_steps": 0.0-1.0}}
}}"""
        return self.client.extract(SYSTEM_PROMPT, prompt)


class LegalAIExtractor(BaseExtractor):
    tier = ExtractionTier.TIER_2
    name = "ai_legal"

    def __init__(self, client: AnthropicClient | None = None) -> None:
        self.client = client or AnthropicClient()

    def extract(self, section_text: str, section_id: str, tables=None) -> dict[str, Any]:
        prompt = f"""Extract legal provisions from this Official Statement section titled "{section_id}":

{section_text[:8000]}

Return a JSON object with these exact fields:
{{
  "governing_law_state": "state or null",
  "events_of_default": ["list of default triggers"],
  "remedies_upon_default": ["list of remedies"],
  "bondholders_rights": "percentage needed for action or null",
  "amendment_provisions": "consent thresholds or null",
  "defeasance_permitted": true/false,
  "defeasance_type": "legal|economic|crossover|not_permitted or null",
  "_confidence": {{field_name: 0.0-1.0 for each field}}
}}"""
        return self.client.extract(SYSTEM_PROMPT, prompt)


class ContinuingDisclosureAIExtractor(BaseExtractor):
    tier = ExtractionTier.TIER_2
    name = "ai_continuing_disclosure"

    def __init__(self, client: AnthropicClient | None = None) -> None:
        self.client = client or AnthropicClient()

    def extract(self, section_text: str, section_id: str, tables=None) -> dict[str, Any]:
        prompt = f"""Extract continuing disclosure information from this Official Statement section titled "{section_id}":

{section_text[:6000]}

Return a JSON object with these exact fields:
{{
  "annual_filing_required": true/false,
  "annual_filing_contents": ["list of what's included in annual filing"],
  "material_event_notices": true/false,
  "emma_filing_commitment": true/false,
  "prior_compliance_history": "description or null",
  "_confidence": {{field_name: 0.0-1.0 for each field}}
}}"""
        return self.client.extract(SYSTEM_PROMPT, prompt)


class UnderwritingAIExtractor(BaseExtractor):
    tier = ExtractionTier.TIER_2
    name = "ai_underwriting"

    def __init__(self, client: AnthropicClient | None = None) -> None:
        self.client = client or AnthropicClient()

    def extract(self, section_text: str, section_id: str, tables=None) -> dict[str, Any]:
        prompt = f"""Extract underwriting terms from this Official Statement section titled "{section_id}":

{section_text[:6000]}

Return a JSON object with these exact fields:
{{
  "sale_type": "competitive|negotiated|private_placement or null",
  "underwriter_discount_per_bond": number or null,
  "management_fee": number or null,
  "takedown": number or null,
  "total_spread": number or null,
  "_confidence": {{field_name: 0.0-1.0 for each field}}
}}"""
        return self.client.extract(SYSTEM_PROMPT, prompt)


class RevenueStreamsAIExtractor(BaseExtractor):
    tier = ExtractionTier.TIER_2
    name = "ai_revenue_streams"

    def __init__(self, client: AnthropicClient | None = None) -> None:
        self.client = client or AnthropicClient()

    def extract(self, section_text: str, section_id: str, tables=None) -> dict[str, Any]:
        prompt = f"""Extract revenue stream and contract details from this Official Statement section titled "{section_id}":

{section_text[:12000]}

Look for these four types of revenue arrangements. For each type, extract ALL instances found.

1. TIPPING FEES / DISPOSAL FEES / GATE RATES:
   - Per-ton or per-cubic-yard rates, flat annual fees, tiered structures
   - Rate escalation (CPI, fixed %, contractual)
   - Minimum annual tonnage (put-or-pay provisions)
   - Flow control ordinances directing waste to the facility
   - Counterparty municipalities or haulers
   - Contract terms and expiration dates

2. ELECTRICITY PPAs / POWER PURCHASE AGREEMENTS:
   - Counterparty utility or offtaker name and credit rating
   - Price per kWh or MWh, escalation mechanism
   - Capacity (MW), estimated annual generation (MWh)
   - Dispatch priority (must-take, baseload, as-available)
   - Minimum delivery obligations, curtailment provisions
   - Whether assigned as security for the bonds

3. CARBON CREDITS / EMISSION PROGRAMS:
   - Program type: compliance (cap-and-trade), voluntary offsets, renewable energy credits
   - Registry (California ARB, Verra, Gold Standard, etc.)
   - Credit type (CERs, VERs, RECs, RINs, D3 RINs, etc.)
   - Estimated annual credits, price per credit, price floors
   - Counterparty and contract terms

4. OFFTAKE AGREEMENTS (non-electricity products):
   - Product: steam, metals, ash, biogas, RNG, hydrogen, recyclables, compost, water, chemicals, aggregate
   - Counterparty name and credit rating
   - Pricing mechanism (fixed, market-indexed, formula)
   - Take-or-pay provisions, minimum purchase obligations
   - Estimated annual revenue, contract terms

Return a JSON object with these exact fields:
{{
  "tipping_fees": [
    {{
      "fee_type": "per_ton|per_cubic_yard|flat_annual|tiered or null",
      "current_rate": number or null,
      "rate_escalator_type": "cpi|fixed_pct|contractual|market or null",
      "rate_escalator_pct": number or null,
      "minimum_annual_tonnage": number or null,
      "guaranteed_annual_revenue": number or null,
      "contract_term_years": number or null,
      "contract_expiry_date": "YYYY-MM-DD or null",
      "counterparties": ["list of municipality/hauler names"],
      "put_or_pay": true/false,
      "flow_control_ordinance": true/false
    }}
  ],
  "electricity_ppas": [
    {{
      "counterparty": "name or null",
      "counterparty_credit_rating": "rating or null",
      "contract_term_years": number or null,
      "contract_start_date": "YYYY-MM-DD or null",
      "contract_expiry_date": "YYYY-MM-DD or null",
      "price_per_kwh": number or null,
      "price_per_mwh": number or null,
      "price_escalator_type": "cpi|fixed_pct|market_indexed|none or null",
      "price_escalator_pct": number or null,
      "capacity_mw": number or null,
      "estimated_annual_generation_mwh": number or null,
      "minimum_delivery_obligation_mwh": number or null,
      "curtailment_provisions": true/false,
      "dispatch_priority": "must_take|baseload|dispatchable|as_available or null",
      "assigned_as_security": true/false
    }}
  ],
  "carbon_credits": [
    {{
      "program_type": "compliance|voluntary|cap_and_trade|offset or null",
      "registry": "registry name or null",
      "credit_type": "credit type or null",
      "estimated_annual_credits": number or null,
      "price_per_credit": number or null,
      "price_floor": number or null,
      "price_escalator_pct": number or null,
      "contract_term_years": number or null,
      "counterparty": "name or null",
      "assigned_as_security": true/false,
      "revenue_share_pct": number or null
    }}
  ],
  "offtake_agreements": [
    {{
      "product_type": "steam|processed_materials|compost|recyclables|metals|ash|biogas|rng|hydrogen|water|chemicals|aggregate|other or null",
      "counterparty": "name or null",
      "counterparty_credit_rating": "rating or null",
      "contract_term_years": number or null,
      "contract_expiry_date": "YYYY-MM-DD or null",
      "pricing_mechanism": "fixed|market_indexed|formula|negotiated or null",
      "minimum_purchase_obligation": number or null,
      "estimated_annual_revenue": number or null,
      "assigned_as_security": true/false,
      "take_or_pay": true/false
    }}
  ],
  "total_contracted_revenue_pct": number or null,
  "revenue_concentration_risk": "low|moderate|high or null",
  "shortest_contract_expiry": "YYYY-MM-DD or null",
  "has_put_or_pay": true/false,
  "has_flow_control": true/false,
  "has_take_or_pay": true/false,
  "_confidence": {{"tipping_fees": 0.0-1.0, "electricity_ppas": 0.0-1.0, "carbon_credits": 0.0-1.0, "offtake_agreements": 0.0-1.0}}
}}

If none of these revenue stream types are described in the text, return empty lists for each type."""
        return self.client.extract(SYSTEM_PROMPT, prompt)


class OperationalMetricsAIExtractor(BaseExtractor):
    """Extracts DSCR, debt service schedules, generation volumes, escalation rates, and operating expenses."""
    tier = ExtractionTier.TIER_2
    name = "ai_operational_metrics"

    def __init__(self, client: AnthropicClient | None = None) -> None:
        self.client = client or AnthropicClient()

    def extract(self, section_text: str, section_id: str, tables=None) -> dict[str, Any]:
        prompt = f"""Extract operational and financial metrics from this Official Statement section titled "{section_id}":

{section_text[:12000]}

Extract ALL of the following data points. These are critical for financial modeling.

1. DEBT SERVICE COVERAGE RATIO (DSCR):
   - Historical DSCR values by year
   - Projected DSCR values by year
   - Minimum required DSCR (from rate covenant)
   - Additional bonds test DSCR requirement

2. DEBT SERVICE SCHEDULE:
   - Annual principal payments by year
   - Annual interest payments by year
   - Total annual debt service by year
   - Maximum annual debt service (MADS)

3. ELECTRICITY GENERATION:
   - Annual generation in MWh (not just MW capacity)
   - Capacity factor percentage
   - Net generation vs gross generation
   - Historical generation volumes if available

4. TIPPING FEE / DISPOSAL FEE ESCALATION:
   - Current rate per ton
   - Annual escalation rate (% or CPI-linked)
   - Escalation mechanism (fixed %, CPI, contractual schedule)
   - Historical rate increases if shown

5. OPERATING EXPENSES:
   - Total annual operating expenses
   - O&M expenses breakdown if available
   - Operating expense per ton or per unit
   - Historical operating expense trend (year-over-year)
   - Projected operating expenses

Return a JSON object with these exact fields:
{{
  "dscr": {{
    "historical": [{{"year": 2024, "dscr": 1.35}}, ...],
    "projected": [{{"year": 2025, "dscr": 1.30}}, ...],
    "minimum_required": number or null,
    "additional_bonds_test": number or null
  }},
  "debt_service_schedule": [
    {{"year": 2025, "principal": number, "interest": number, "total": number}}
  ],
  "maximum_annual_debt_service": number or null,
  "electricity_generation": {{
    "annual_mwh": number or null,
    "capacity_factor_pct": number or null,
    "capacity_mw": number or null,
    "net_generation_mwh": number or null,
    "historical_mwh": [{{"year": 2024, "mwh": number}}, ...]
  }},
  "tipping_fee_escalation": {{
    "current_rate_per_ton": number or null,
    "escalation_rate_pct": number or null,
    "escalation_mechanism": "fixed_pct|cpi|contractual_schedule|market or null",
    "historical_rates": [{{"year": 2024, "rate": number}}, ...]
  }},
  "operating_expenses": {{
    "total_annual": number or null,
    "per_ton": number or null,
    "historical": [{{"year": 2024, "amount": number}}, ...],
    "projected": [{{"year": 2025, "amount": number}}, ...],
    "categories": {{"labor": number, "maintenance": number, "utilities": number, "other": number}} or null
  }},
  "_confidence": {{"dscr": 0.0-1.0, "debt_service": 0.0-1.0, "generation": 0.0-1.0, "escalation": 0.0-1.0, "opex": 0.0-1.0}}
}}

If a data point is not described in the text, use null. Do not infer or estimate."""
        return self.client.extract(SYSTEM_PROMPT, prompt)


class RefundingAIExtractor(BaseExtractor):
    tier = ExtractionTier.TIER_2
    name = "ai_refunding"

    def __init__(self, client: AnthropicClient | None = None) -> None:
        self.client = client or AnthropicClient()

    def extract(self, section_text: str, section_id: str, tables=None) -> dict[str, Any]:
        prompt = f"""Determine if this is a refunding deal and extract refunding information from this Official Statement section titled "{section_id}":

{section_text[:6000]}

Return a JSON object with these exact fields:
{{
  "is_refunding": true/false,
  "refunding_type": "advance_refunding|current_refunding|crossover_refunding|none or null",
  "refunded_bonds_series": ["list of refunded series"],
  "refunded_bonds_original_par": number or null,
  "present_value_savings": number or null,
  "savings_as_percentage": number or null,
  "_confidence": {{field_name: 0.0-1.0 for each field}}
}}"""
        return self.client.extract(SYSTEM_PROMPT, prompt)


# ---------------------------------------------------------------------------
# Cached AI extractor wrapper
# ---------------------------------------------------------------------------

class CachedAIExtractor:
    """Wraps any AI extractor with cache support."""

    def __init__(self, extractor: BaseExtractor, doc_hash: str) -> None:
        self.extractor = extractor
        self.doc_hash = doc_hash
        settings = get_settings()
        self.cache_dir = settings.cache_dir
        self.cache_enabled = settings.ai_cache_enabled
        self.cache_ttl = settings.cache_ttl_days

    def extract(
        self,
        section_text: str,
        section_id: str,
        tables: list[list[list[str]]] | None = None,
    ) -> dict[str, Any]:
        if self.cache_enabled:
            key = compute_cache_key(self.doc_hash, section_id, self.extractor.name)
            cached = load_from_cache(self.cache_dir, key, self.cache_ttl)
            if cached is not None:
                logger.debug("Cache hit for %s/%s", self.extractor.name, section_id)
                return cached

        result = self.extractor.safe_extract(section_text, section_id, tables)

        if self.cache_enabled and result:
            key = compute_cache_key(self.doc_hash, section_id, self.extractor.name)
            save_to_cache(self.cache_dir, key, result)

        return result


# ---------------------------------------------------------------------------
# Section -> Extractor mapping
# ---------------------------------------------------------------------------

# Maps section IDs to which AI extractors should run on them
SECTION_EXTRACTOR_MAP: dict[str, list[type[BaseExtractor]]] = {
    "COVER_PAGE": [DealIdentityAIExtractor, DealStructureAIExtractor],
    "INTRODUCTION_AND_SUMMARY": [DealIdentityAIExtractor, DealStructureAIExtractor, RefundingAIExtractor, RevenueStreamsAIExtractor, OperationalMetricsAIExtractor],
    "THE_BONDS": [DealStructureAIExtractor],
    "PLAN_OF_FINANCE": [RefundingAIExtractor],
    "THE_ISSUER": [DealIdentityAIExtractor],
    "THE_BORROWER": [DealIdentityAIExtractor],
    "SECURITY_FOR_THE_BONDS": [SecurityAIExtractor, RevenueStreamsAIExtractor, OperationalMetricsAIExtractor],
    "FLOW_OF_FUNDS": [FlowOfFundsAIExtractor, RevenueStreamsAIExtractor],
    "RATE_COVENANT": [SecurityAIExtractor, OperationalMetricsAIExtractor],
    "ADDITIONAL_BONDS_TEST": [SecurityAIExtractor],
    "THE_PROJECT": [RevenueStreamsAIExtractor, OperationalMetricsAIExtractor],
    "DEBT_SERVICE_SCHEDULE": [OperationalMetricsAIExtractor],
    "FINANCIAL_INFORMATION": [OperationalMetricsAIExtractor],
    "SERVICE_AGREEMENTS": [RevenueStreamsAIExtractor],
    "RISK_FACTORS": [RiskFactorsAIExtractor],
    "LEGAL_MATTERS": [LegalAIExtractor],
    "UNDERWRITING": [UnderwritingAIExtractor],
    "CONTINUING_DISCLOSURE": [ContinuingDisclosureAIExtractor],
}
