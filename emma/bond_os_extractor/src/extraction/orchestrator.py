from __future__ import annotations

import logging
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

from ..config import get_settings
from ..ingestion.pdf_reader import IngestionResult, extract_pdf
from ..ingestion.section_detector import DocumentSection, detect_sections
from ..schema.deal_identity import DealIdentity
from ..schema.deal_structure import DealStructure, MaturitySchedule, MaturityRow
from ..schema.security import (
    AdditionalBondsTest,
    DebtServiceReserve,
    RateCovenant,
    SecurityPackage,
)
from ..schema.financials import (
    DebtServiceRow,
    DebtServiceSchedule,
    SourcesAndUses,
)
from ..schema.additional import (
    ContinuingDisclosureProfile,
    FlowOfFunds,
    LegalProvisions,
    Rating,
    RatingProfile,
    RefundingInfo,
    RiskFactor,
    RiskFactorProfile,
    UnderwritingTerms,
    WaterfallStep,
)
from ..schema.deal_record import DealRecord, ReviewFlag
from .deterministic import ALL_DETERMINISTIC_EXTRACTORS
from .table_extractor import ALL_TABLE_EXTRACTORS
from .ai_extractor import (
    AnthropicClient,
    CachedAIExtractor,
    SECTION_EXTRACTOR_MAP,
)

logger = logging.getLogger("bond_os_extractor.orchestrator")


class ExtractionOrchestrator:
    """Coordinates the full extraction pipeline for one document."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self._ai_client: AnthropicClient | None = None

    @property
    def ai_client(self) -> AnthropicClient:
        if self._ai_client is None:
            self._ai_client = AnthropicClient()
        return self._ai_client

    def extract_document(self, pdf_path: Path) -> DealRecord:
        """Run the full extraction pipeline on a single PDF."""
        pdf_path = Path(pdf_path).resolve()
        extraction_id = str(uuid.uuid4())
        logger.info("Starting extraction %s for %s", extraction_id[:8], pdf_path.name)

        # Step 1: Ingest
        ingestion = extract_pdf(pdf_path)
        if ingestion.extraction_method == "failed":
            logger.error("Ingestion failed for %s", pdf_path.name)
            return DealRecord(
                extraction_id=extraction_id,
                source_file=pdf_path.name,
                source_hash=ingestion.source_hash,
                extraction_timestamp=datetime.now(timezone.utc),
                review_flags=[ReviewFlag(
                    field_path="ingestion",
                    issue="All PDF extraction methods failed",
                    confidence=0.0,
                )],
            )

        # Step 2: Detect sections
        sections = detect_sections(ingestion)
        section_map = {s.section_id: s for s in sections}
        logger.info("Detected %d sections", len(sections))

        # Step 3: Run Tier 1 (deterministic) extractors
        tier1_results = self._run_tier1(ingestion, sections)
        logger.info("Tier 1 extracted %d fields", sum(len(v) for v in tier1_results.values()))

        # Step 4: Run Tier 2 (AI) extractors
        tier2_results: dict[str, dict[str, Any]] = {}
        if self.settings.tier2_enabled and self.settings.anthropic_api_key:
            tier2_results = self._run_tier2(ingestion.source_hash, sections)
            logger.info("Tier 2 extracted %d field groups", len(tier2_results))
        else:
            logger.info("Tier 2 skipped (disabled or no API key)")

        # Step 5: Merge results into DealRecord
        record = self._assemble_record(
            extraction_id, ingestion, tier1_results, tier2_results,
        )

        # Step 6: Compute completeness
        record.compute_completeness()
        logger.info(
            "Extraction complete for %s — completeness: %.1f%%",
            pdf_path.name, record.completeness_score * 100,
        )

        return record

    # ------------------------------------------------------------------
    # Tier 1
    # ------------------------------------------------------------------

    def _run_tier1(
        self,
        ingestion: IngestionResult,
        sections: list[DocumentSection],
    ) -> dict[str, dict[str, Any]]:
        """Run all deterministic extractors on relevant sections."""
        results: dict[str, dict[str, Any]] = {}

        # Collect all tables from all pages
        all_tables: list[list[list[str]]] = []
        for page in ingestion.pages:
            all_tables.extend(page.tables)

        # Deterministic extractors run on cover/intro/full text
        cover_text = ""
        for s in sections:
            if s.section_id in ("COVER_PAGE", "INTRODUCTION_AND_SUMMARY", "FULL_DOCUMENT"):
                cover_text += s.text + "\n\n"
        if not cover_text:
            cover_text = "\n\n".join(p.text for p in ingestion.pages[:5])

        for extractor_cls in ALL_DETERMINISTIC_EXTRACTORS:
            ext = extractor_cls()
            result = ext.safe_extract(cover_text, "COVER_PAGE")
            if result:
                results[ext.name] = result

        # Table extractors run on all tables
        for extractor_cls in ALL_TABLE_EXTRACTORS:
            ext = extractor_cls()
            # Try section-specific tables first, then all tables
            for section in sections:
                if section.section_id in (
                    "SOURCES_AND_USES", "DEBT_SERVICE_SCHEDULE",
                    "COVER_PAGE", "THE_BONDS",
                ):
                    # Gather tables from pages in this section
                    section_tables: list[list[list[str]]] = []
                    for page in ingestion.pages:
                        if section.start_page <= page.page_number <= section.end_page:
                            section_tables.extend(page.tables)
                    if section_tables:
                        result = ext.safe_extract(section.text, section.section_id, section_tables)
                        if result:
                            results[f"{ext.name}_{section.section_id}"] = result

            # Also try on all tables as fallback
            if all_tables:
                full_text = "\n\n".join(p.text for p in ingestion.pages)
                result = ext.safe_extract(full_text, "FULL_DOCUMENT", all_tables)
                if result and ext.name not in results:
                    results[ext.name] = result

        return results

    # ------------------------------------------------------------------
    # Tier 2
    # ------------------------------------------------------------------

    def _run_tier2(
        self,
        doc_hash: str,
        sections: list[DocumentSection],
    ) -> dict[str, dict[str, Any]]:
        """Run AI extractors on their mapped sections."""
        results: dict[str, dict[str, Any]] = {}

        for section in sections:
            extractor_classes = SECTION_EXTRACTOR_MAP.get(section.section_id, [])
            for ext_cls in extractor_classes:
                ext = ext_cls(client=self.ai_client)
                cached_ext = CachedAIExtractor(ext, doc_hash)
                key = f"{ext.name}_{section.section_id}"
                try:
                    result = cached_ext.extract(section.text, section.section_id)
                    if result:
                        results[key] = result
                except Exception as exc:
                    logger.warning(
                        "AI extractor %s failed on %s: %s",
                        ext.name, section.section_id, exc,
                    )

        return results

    # ------------------------------------------------------------------
    # Assembly
    # ------------------------------------------------------------------

    def _assemble_record(
        self,
        extraction_id: str,
        ingestion: IngestionResult,
        tier1: dict[str, dict[str, Any]],
        tier2: dict[str, dict[str, Any]],
    ) -> DealRecord:
        """Merge all extraction results into a single DealRecord."""
        record = DealRecord(
            extraction_id=extraction_id,
            source_file=ingestion.source_file,
            source_hash=ingestion.source_hash,
            extraction_timestamp=datetime.now(timezone.utc),
        )
        confidence: dict[str, float] = {}
        flags: list[ReviewFlag] = []

        # Merge all results
        all_results = {**tier1, **tier2}

        # Helper to safely convert to Decimal
        def _dec(val: Any) -> Decimal | None:
            if val is None:
                return None
            try:
                return Decimal(str(val))
            except Exception:
                return None

        # Helper to safely convert to date
        def _date(val: Any) -> date | None:
            if val is None:
                return None
            if isinstance(val, date):
                return val
            try:
                from dateutil import parser as dateparser
                return dateparser.parse(str(val)).date()
            except Exception:
                return None

        # -- Identity --
        identity = DealIdentity()
        for key, data in all_results.items():
            conf = data.pop("_confidence", {})
            confidence.update({f"{key}.{k}": v for k, v in conf.items()})

            if "issuer_name" in data and not identity.issuer_name:
                identity.issuer_name = data["issuer_name"]
            if "issuer_type" in data and not identity.issuer_type:
                identity.issuer_type = data.get("issuer_type")
            if "issuer_state" in data and not identity.issuer_state:
                identity.issuer_state = data.get("issuer_state")
            if "issuer_county" in data:
                identity.issuer_county = data.get("issuer_county")
            if "borrower_name" in data:
                identity.borrower_name = data.get("borrower_name")
            if "borrower_type" in data:
                identity.borrower_type = data.get("borrower_type")
            if "trustee_name" in data:
                identity.trustee_name = data.get("trustee_name")
            if "bond_counsel" in data:
                identity.bond_counsel = data.get("bond_counsel")
            if "underwriter_names" in data and not identity.underwriter_names:
                identity.underwriter_names = data.get("underwriter_names", [])
            if "underwriter_counsel" in data:
                identity.underwriter_counsel = data.get("underwriter_counsel")
            if "municipal_advisor" in data:
                identity.municipal_advisor = data.get("municipal_advisor")
            if "disclosure_counsel" in data:
                identity.disclosure_counsel = data.get("disclosure_counsel")
            if "paying_agent" in data:
                identity.paying_agent = data.get("paying_agent")
            if "registrar" in data:
                identity.registrar = data.get("registrar")
            if "verification_agent" in data:
                identity.verification_agent = data.get("verification_agent")
            if "cusip_base" in data and not identity.cusip_base:
                identity.cusip_base = data.get("cusip_base")
            if "cusip_series" in data and not identity.cusip_series:
                identity.cusip_series = data.get("cusip_series", [])
            if "document_type" in data and not identity.document_type:
                identity.document_type = data.get("document_type")
            if "dated_date" in data and not identity.dated_date:
                identity.dated_date = _date(data.get("dated_date"))
            if "delivery_date" in data and not identity.delivery_date:
                identity.delivery_date = _date(data.get("delivery_date"))
            if "sale_date" in data and not identity.sale_date:
                identity.sale_date = _date(data.get("sale_date"))
            if "series_name" in data and not identity.series_name:
                identity.series_name = data.get("series_name")
            if "official_title" in data and not identity.official_title:
                identity.official_title = data.get("official_title")

        record.identity = identity

        # -- Structure --
        structure = DealStructure()
        for key, data in all_results.items():
            if "par_amount" in data and not structure.par_amount:
                structure.par_amount = _dec(data["par_amount"])
            if "bond_type" in data and not structure.bond_type:
                structure.bond_type = data.get("bond_type")
            if "tax_status" in data and not structure.tax_status:
                structure.tax_status = data.get("tax_status")
            if "interest_type" in data and not structure.interest_type:
                structure.interest_type = data.get("interest_type")
            if "denomination" in data:
                structure.denomination = _dec(data.get("denomination"))
            if "cab_enabled" in data:
                structure.cab_enabled = bool(data.get("cab_enabled"))
            if "slb_enabled" in data:
                structure.slb_enabled = bool(data.get("slb_enabled"))
            if "green_bond" in data:
                structure.green_bond = bool(data.get("green_bond"))
            if "social_bond" in data:
                structure.social_bond = bool(data.get("social_bond"))
            if "sustainability_bond" in data:
                structure.sustainability_bond = bool(data.get("sustainability_bond"))
            if "maturity_type" in data and not structure.maturity_type:
                structure.maturity_type = data.get("maturity_type")
            if "final_maturity_date" in data and not structure.final_maturity_date:
                structure.final_maturity_date = _date(data.get("final_maturity_date"))
            if "optional_redemption_date" in data:
                structure.optional_redemption_date = _date(data.get("optional_redemption_date"))
            if "optional_redemption_price" in data:
                structure.optional_redemption_price = _dec(data.get("optional_redemption_price"))
            if "make_whole_call" in data:
                structure.make_whole_call = bool(data.get("make_whole_call"))
            if "extraordinary_redemption" in data:
                structure.extraordinary_redemption = bool(data.get("extraordinary_redemption"))
            if "mandatory_sinking_fund" in data:
                structure.mandatory_sinking_fund = bool(data.get("mandatory_sinking_fund"))
            if "turbo_redemption" in data:
                structure.turbo_redemption = bool(data.get("turbo_redemption"))
            if "credit_enhancement_type" in data:
                structure.credit_enhancement_type = data.get("credit_enhancement_type")
            if "credit_enhancer_name" in data:
                structure.credit_enhancer_name = data.get("credit_enhancer_name")

        record.structure = structure

        # -- Maturity Schedule --
        for key, data in all_results.items():
            if "maturity_schedule" in data and record.maturity_schedule is None:
                ms_data = data["maturity_schedule"]
                rows = []
                for r in ms_data.get("rows") or []:
                    rows.append(MaturityRow(
                        maturity_date=_date(r.get("maturity_date")),
                        par_amount=_dec(r.get("par_amount")),
                        coupon_rate=_dec(r.get("coupon_rate")),
                        yield_to_maturity=_dec(r.get("yield_to_maturity")),
                        price=_dec(r.get("price")),
                        cusip=r.get("cusip"),
                    ))
                record.maturity_schedule = MaturitySchedule(
                    rows=rows,
                    total_par=_dec(ms_data.get("total_par")),
                )

        # -- Security Package --
        for key, data in all_results.items():
            if "pledge_type" in data and record.security is None:
                try:
                    rc = None
                    if data.get("rate_covenant"):
                        rc_data = data["rate_covenant"]
                        rc = RateCovenant(
                            covenant_type=rc_data.get("covenant_type"),
                            minimum_coverage_ratio=_dec(rc_data.get("minimum_coverage_ratio")),
                            coverage_calculation_basis=rc_data.get("coverage_calculation_basis"),
                            consultant_rate_study_required=bool(rc_data.get("consultant_rate_study_required")),
                            cure_period_days=rc_data.get("cure_period_days"),
                        )
                    abt = None
                    if data.get("additional_bonds_test"):
                        abt_data = data["additional_bonds_test"]
                        abt = AdditionalBondsTest(
                            historical_coverage_required=_dec(abt_data.get("historical_coverage_required")),
                            projected_coverage_required=_dec(abt_data.get("projected_coverage_required")),
                            lookback_period_years=abt_data.get("lookback_period_years"),
                            consultant_certification_required=bool(abt_data.get("consultant_certification_required")),
                        )
                    dsr = None
                    if data.get("debt_service_reserve_fund"):
                        dsr_data = data["debt_service_reserve_fund"]
                        dsr = DebtServiceReserve(
                            requirement_type=dsr_data.get("requirement_type"),
                            amount=_dec(dsr_data.get("amount")),
                            funded_at_closing=bool(dsr_data.get("funded_at_closing")),
                            surety_bond_permitted=bool(dsr_data.get("surety_bond_permitted")),
                        )
                    record.security = SecurityPackage(
                        pledge_type=data.get("pledge_type"),
                        pledged_revenues_description=data.get("pledged_revenues_description"),
                        lien_position=data.get("lien_position"),
                        real_property_mortgage=bool(data.get("real_property_mortgage")),
                        equipment_security_interest=bool(data.get("equipment_security_interest")),
                        offtake_agreements_assigned=bool(data.get("offtake_agreements_assigned")),
                        offtake_counterparties=data.get("offtake_counterparties") or [],
                        rate_covenant=rc,
                        additional_bonds_test=abt,
                        debt_service_reserve_fund=dsr,
                    )
                except Exception as exc:
                    logger.warning("Failed to assemble security: %s", exc)

        # -- Debt Service --
        for key, data in all_results.items():
            if "debt_service" in data and record.debt_service is None:
                try:
                    ds_data = data["debt_service"]
                    rows = []
                    for r in ds_data.get("rows") or []:
                        rows.append(DebtServiceRow(
                            fiscal_year=r.get("fiscal_year", 0),
                            principal=_dec(r.get("principal")),
                            interest=_dec(r.get("interest")),
                            total=_dec(r.get("total")),
                            outstanding_balance=_dec(r.get("outstanding_balance")),
                        ))
                    record.debt_service = DebtServiceSchedule(
                        rows=rows,
                        total_principal=_dec(ds_data.get("total_principal")),
                        total_interest=_dec(ds_data.get("total_interest")),
                        total_debt_service=_dec(ds_data.get("total_debt_service")),
                        maximum_annual_debt_service=_dec(ds_data.get("maximum_annual_debt_service")),
                    )
                except Exception as exc:
                    logger.warning("Failed to assemble debt_service: %s", exc)

        # -- Sources & Uses --
        for key, data in all_results.items():
            if "sources_uses" in data and record.sources_uses is None:
                try:
                    su_data = data["sources_uses"]
                    record.sources_uses = SourcesAndUses(
                        bond_proceeds=_dec(su_data.get("bond_proceeds")),
                        original_issue_premium=_dec(su_data.get("original_issue_premium")),
                        project_fund_deposit=_dec(su_data.get("project_fund_deposit")),
                        debt_service_reserve_deposit=_dec(su_data.get("debt_service_reserve_deposit")),
                        capitalized_interest=_dec(su_data.get("capitalized_interest")),
                        costs_of_issuance=_dec(su_data.get("costs_of_issuance")),
                        underwriter_discount=_dec(su_data.get("underwriter_discount")),
                        total_sources=_dec(su_data.get("total_sources")),
                        total_uses=_dec(su_data.get("total_uses")),
                    )
                except Exception as exc:
                    logger.warning("Failed to assemble sources_uses: %s", exc)

        # -- Ratings --
        for key, data in all_results.items():
            if "ratings" in data and record.ratings is None:
                try:
                    rating_list = data["ratings"]
                    if isinstance(rating_list, list):
                        record.ratings = RatingProfile(
                            ratings=[Rating(**r) for r in rating_list if isinstance(r, dict)],
                        )
                except Exception as exc:
                    logger.warning("Failed to assemble ratings: %s", exc)

        # -- Risk Factors --
        for key, data in all_results.items():
            if "risks" in data and record.risk_factors is None:
                try:
                    record.risk_factors = RiskFactorProfile(
                        risks=[RiskFactor(**r) for r in (data.get("risks") or []) if isinstance(r, dict)],
                        total_risk_factors_count=data.get("total_risk_factors_count", 0),
                        has_project_specific_risks=bool(data.get("has_project_specific_risks")),
                        has_technology_risk=bool(data.get("has_technology_risk")),
                        has_construction_risk=bool(data.get("has_construction_risk")),
                        has_environmental_compliance_risk=bool(data.get("has_environmental_compliance_risk")),
                    )
                except Exception as exc:
                    logger.warning("Failed to assemble risk_factors: %s", exc)

        # -- Flow of Funds --
        for key, data in all_results.items():
            if "waterfall_steps" in data and record.flow_of_funds is None:
                try:
                    record.flow_of_funds = FlowOfFunds(
                        waterfall_steps=[WaterfallStep(**s) for s in (data.get("waterfall_steps") or []) if isinstance(s, dict)],
                        trapped_cash_provisions=bool(data.get("trapped_cash_provisions")),
                        sweep_to_equity_permitted=bool(data.get("sweep_to_equity_permitted")),
                    )
                except Exception as exc:
                    logger.warning("Failed to assemble flow_of_funds: %s", exc)

        # -- Legal Provisions --
        for key, data in all_results.items():
            if "events_of_default" in data and record.legal_provisions is None:
                try:
                    record.legal_provisions = LegalProvisions(
                        governing_law_state=data.get("governing_law_state"),
                        events_of_default=data.get("events_of_default") or [],
                        remedies_upon_default=data.get("remedies_upon_default") or [],
                        bondholders_rights=data.get("bondholders_rights"),
                        amendment_provisions=data.get("amendment_provisions"),
                        defeasance_permitted=bool(data.get("defeasance_permitted")),
                        defeasance_type=data.get("defeasance_type"),
                    )
                except Exception as exc:
                    logger.warning("Failed to assemble legal_provisions: %s", exc)

        # -- Continuing Disclosure --
        for key, data in all_results.items():
            if "annual_filing_required" in data and record.continuing_disclosure is None:
                try:
                    record.continuing_disclosure = ContinuingDisclosureProfile(
                        annual_filing_required=bool(data.get("annual_filing_required")),
                        annual_filing_contents=data.get("annual_filing_contents") or [],
                        material_event_notices=bool(data.get("material_event_notices")),
                        emma_filing_commitment=bool(data.get("emma_filing_commitment")),
                        prior_compliance_history=data.get("prior_compliance_history"),
                    )
                except Exception as exc:
                    logger.warning("Failed to assemble continuing_disclosure: %s", exc)

        # -- Underwriting --
        for key, data in all_results.items():
            if "sale_type" in data and record.underwriting is None:
                try:
                    record.underwriting = UnderwritingTerms(
                        sale_type=data.get("sale_type"),
                        underwriter_discount_per_bond=_dec(data.get("underwriter_discount_per_bond")),
                        management_fee=_dec(data.get("management_fee")),
                        takedown=_dec(data.get("takedown")),
                        total_spread=_dec(data.get("total_spread")),
                    )
                except Exception as exc:
                    logger.warning("Failed to assemble underwriting: %s", exc)

        # -- Refunding --
        for key, data in all_results.items():
            if "is_refunding" in data and data.get("is_refunding") and record.refunding is None:
                try:
                    record.refunding = RefundingInfo(
                        is_refunding=True,
                        refunding_type=data.get("refunding_type"),
                        refunded_bonds_series=data.get("refunded_bonds_series") or [],
                        refunded_bonds_original_par=_dec(data.get("refunded_bonds_original_par")),
                        present_value_savings=_dec(data.get("present_value_savings")),
                        savings_as_percentage=_dec(data.get("savings_as_percentage")),
                    )
                except Exception as exc:
                    logger.warning("Failed to assemble refunding: %s", exc)

        record.confidence_scores = confidence
        record.review_flags = flags
        return record
