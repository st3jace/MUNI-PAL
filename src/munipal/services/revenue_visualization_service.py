"""
Revenue diversification visualization assembler.

Builds a typed visualization payload from approved project facts so the same
contract can power dashboard rendering, export, and later packet assembly.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from math import ceil
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from munipal.core.models.fact import ExtractedFact
from munipal.core.models.project import Project
from munipal.core.schemas.base import ReviewStatus
from munipal.core.schemas.revenue_visualization import (
    RevenueDiversificationVisualizationResponse,
    RevenueDiversificationRiskProof,
    RevenueScenarioMix,
    RevenueScenarioSafety,
    RevenueRiskProofMetric,
    RevenueStabilityClass,
    RevenueStreamDefinition,
    RevenueStreamSlice,
)
from munipal.services.fact_service import FactService


@dataclass(frozen=True)
class _StreamRegistryItem:
    stream_id: str
    label: str
    color: str
    stability_class: RevenueStabilityClass
    description: str
    activation_stage: str
    schema_paths: tuple[str, ...]


@dataclass(frozen=True)
class _ScenarioTemplate:
    scenario_id: str
    label: str
    target_diesel_share: float | None
    activation_stage: str
    inferred_weights: Mapping[str, float]


@dataclass
class _StreamAmount:
    amount: float
    source_path: str | None = None
    is_inferred: bool = False


@dataclass(frozen=True)
class _PacketScenarioOverride:
    scenario_id: str
    label: str
    streams: Mapping[str, float]
    inferred_streams: tuple[str, ...]
    dscr_mean: float
    dscr_minimum: float
    breach_weeks: int
    implied_rating: str
    breakeven_diesel_price: float
    dscr_parity_diesel_price: float
    covenant_trigger_diesel_price: float
    safety_status: RevenueScenarioSafety
    safety_label: str
    assumptions: tuple[str, ...] = ()


CALDOR_PACKET_SCENARIOS: tuple[_PacketScenarioOverride, ...] = (
    _PacketScenarioOverride(
        scenario_id="current_state",
        label="Diesel + Biochar",
        streams={
            "diesel": 10_125_000.0,
            "biochar": 438_750.0,
        },
        inferred_streams=(),
        dscr_mean=1.52,
        dscr_minimum=1.20,
        breach_weeks=25,
        implied_rating="AA",
        breakeven_diesel_price=2.94,
        dscr_parity_diesel_price=4.05,
        covenant_trigger_diesel_price=4.44,
        safety_status=RevenueScenarioSafety.FRAGILE,
        safety_label="Razor-thin",
        assumptions=(
            "DSCR overlay anchored to the packet's S01 CAB Prosperity row: the current diesel-plus-biochar business model is covenant-tight even before a collapse path is applied.",
        ),
    ),
    _PacketScenarioOverride(
        scenario_id="base_case",
        label="+ Electricity PPA",
        streams={
            "diesel": 10_125_000.0,
            "electricity": 4_048_560.0,
            "biochar": 438_750.0,
        },
        inferred_streams=("electricity",),
        dscr_mean=2.04,
        dscr_minimum=1.76,
        breach_weeks=0,
        implied_rating="AAA",
        breakeven_diesel_price=1.14,
        dscr_parity_diesel_price=2.25,
        covenant_trigger_diesel_price=2.64,
        safety_status=RevenueScenarioSafety.SAFE,
        safety_label="Safe",
        assumptions=(
            "The packet does not publish a standalone 312-week '+ Electricity PPA' run, so the DSCR overlay uses the packet's diversified stress-case anchor (S08) while the revenue stack remains the intermediate operating configuration.",
        ),
    ),
    _PacketScenarioOverride(
        scenario_id="full_diversification",
        label="Full Diversification",
        streams={
            "diesel": 10_125_000.0,
            "electricity": 4_048_560.0,
            "tipping": 1_500_000.0,
            "carbon": 750_000.0,
            "biochar": 438_750.0,
        },
        inferred_streams=("electricity", "tipping", "carbon"),
        dscr_mean=3.14,
        dscr_minimum=2.80,
        breach_weeks=0,
        implied_rating="AAA",
        breakeven_diesel_price=0.0,
        dscr_parity_diesel_price=1.05,
        covenant_trigger_diesel_price=1.44,
        safety_status=RevenueScenarioSafety.FORTRESS,
        safety_label="Fortress",
        assumptions=(
            "DSCR overlay anchored to the packet's S03 combined-basis validation: 3.14x mean DSCR, 2.80x minimum, and zero breach weeks once all five revenue streams are active.",
        ),
    ),
)

CALDOR_PACKET_RISK_PROOF = RevenueDiversificationRiskProof(
    title="Diversification Proof (S06 vs S08)",
    baseline_label="S06: Diesel-Only",
    diversified_label="S08: Diversified",
    takeaway="Under the Caldor packet's collapse-path stress test, diversification eliminates breach weeks and upgrades the implied credit profile from distressed to AAA.",
    metrics=[
        RevenueRiskProofMetric(
            metric_id="dscr_mean",
            label="DSCR Mean",
            baseline_value="0.42x",
            diversified_value="2.04x",
            delta_label="+1.62x",
        ),
        RevenueRiskProofMetric(
            metric_id="dscr_minimum",
            label="DSCR Minimum",
            baseline_value="0.19x",
            diversified_value="1.76x",
            delta_label="+1.57x",
        ),
        RevenueRiskProofMetric(
            metric_id="breach_weeks",
            label="Breach Weeks",
            baseline_value="156 of 312",
            diversified_value="0 of 312",
            delta_label="-156",
        ),
        RevenueRiskProofMetric(
            metric_id="max_drawdown",
            label="Maximum Drawdown",
            baseline_value="-33.8%",
            diversified_value="0.0%",
            delta_label="+33.8%",
        ),
        RevenueRiskProofMetric(
            metric_id="implied_rating",
            label="Implied Rating",
            baseline_value="B/CCC",
            diversified_value="AAA",
            delta_label="+10 notches",
        ),
    ],
)


STREAM_REGISTRY: tuple[_StreamRegistryItem, ...] = (
    _StreamRegistryItem(
        stream_id="diesel",
        label="Diesel",
        color="#1D3557",
        stability_class=RevenueStabilityClass.VOLATILE,
        description="Primary but volatile renewable diesel revenue stream.",
        activation_stage="current",
        schema_paths=(
            "revenue.commodities.renewable-diesel",
            "revenue.commodities.renewable_diesel",
            "revenue.commodities.diesel",
            "revenue.streams.diesel",
            "revenue.streams.renewable_diesel",
        ),
    ),
    _StreamRegistryItem(
        stream_id="electricity",
        label="Electricity",
        color="#4EA8DE",
        stability_class=RevenueStabilityClass.STABLE,
        description="Contracted electricity or PPA-backed revenue.",
        activation_stage="base",
        schema_paths=(
            "revenue.commodities.electricity",
            "revenue.streams.electricity",
            "revenue.offtake.electricity.annual_revenue",
        ),
    ),
    _StreamRegistryItem(
        stream_id="tipping",
        label="Tipping",
        color="#2A9D8F",
        stability_class=RevenueStabilityClass.STABLE,
        description="Tipping-fee or inbound feedstock acceptance revenue.",
        activation_stage="base",
        schema_paths=(
            "revenue.commodities.tipping",
            "revenue.streams.tipping",
            "feedstock.revenue.tipping",
        ),
    ),
    _StreamRegistryItem(
        stream_id="carbon",
        label="Carbon",
        color="#6C9A8B",
        stability_class=RevenueStabilityClass.BALANCED,
        description="Carbon-credit and environmental attribute revenue.",
        activation_stage="full",
        schema_paths=(
            "revenue.commodities.carbon",
            "revenue.streams.carbon",
            "revenue.environmental.carbon_credits",
        ),
    ),
    _StreamRegistryItem(
        stream_id="biochar",
        label="Biochar",
        color="#BC6C25",
        stability_class=RevenueStabilityClass.BALANCED,
        description="Biochar and coproduct revenue with moderate market stability.",
        activation_stage="current",
        schema_paths=(
            "revenue.commodities.biochar",
            "revenue.streams.biochar",
        ),
    ),
)

STREAMS_BY_ID = {item.stream_id: item for item in STREAM_REGISTRY}
STREAM_DEFINITION_ORDER = ("diesel", "electricity", "tipping", "carbon", "biochar")
STREAM_RENDER_ORDER = ("tipping", "electricity", "carbon", "biochar", "diesel")

SCENARIO_TEMPLATES: tuple[_ScenarioTemplate, ...] = (
    _ScenarioTemplate(
        scenario_id="current_state",
        label="Current State",
        target_diesel_share=None,
        activation_stage="current",
        inferred_weights={},
    ),
    _ScenarioTemplate(
        scenario_id="base_case",
        label="Base Case",
        target_diesel_share=0.70,
        activation_stage="base",
        inferred_weights={
            "electricity": 0.82,
            "tipping": 0.18,
        },
    ),
    _ScenarioTemplate(
        scenario_id="full_diversification",
        label="Full Diversification",
        target_diesel_share=0.60,
        activation_stage="full",
        inferred_weights={
            "electricity": 0.58,
            "tipping": 0.23,
            "carbon": 0.11,
            "biochar": 0.08,
        },
    ),
)

AGGREGATE_REVENUE_PATHS: tuple[str, ...] = (
    "revenue.gross.annual",
    "finmodel.inputs.revenue.annual",
)
DSCR_BASE_PATHS: tuple[str, ...] = (
    "finmodel.outputs.dscrbase",
    "finmodel.outputs.dscr.base",
)
DSCR_STRESS_PATHS: tuple[str, ...] = (
    "finmodel.outputs.dscrstress",
    "finmodel.outputs.dscr.stress",
)
COVENANT_TRIGGER_PATHS: tuple[str, ...] = (
    "finmodel.inputs.dscr.minimum",
    "capital_stack.covenants.min_dscr",
)

STAGE_ORDER = {"current": 0, "base": 1, "full": 2}
REFERENCE_DIESEL_PRICE = 4.50


class RevenueVisualizationService:
    """Assemble versioned revenue diversification visualization payloads."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def build_visualization(
        self,
        project_id: UUID,
        mode: str = "auto",
    ) -> RevenueDiversificationVisualizationResponse:
        project = await self.db.get(Project, str(project_id))
        if not project:
            raise ValueError(f"Project {project_id} not found")

        if mode == "packet" or (mode == "auto" and self._matches_caldor_packet(project)):
            return self._build_caldor_packet_visualization(project_id=project_id, project=project)

        facts = await self._list_preferred_facts(project_id)

        explicit_streams = self._extract_explicit_streams(facts)
        current_streams, current_notes = self._build_current_streams(
            explicit_streams=explicit_streams,
            aggregate_revenue=self._first_number(facts, AGGREGATE_REVENUE_PATHS),
        )

        base_streams, base_notes = self._build_future_streams(
            template=SCENARIO_TEMPLATES[1],
            starting_streams=current_streams,
            explicit_streams=explicit_streams,
            aggregate_revenue=self._first_number(facts, AGGREGATE_REVENUE_PATHS),
        )
        full_streams, full_notes = self._build_future_streams(
            template=SCENARIO_TEMPLATES[2],
            starting_streams=base_streams,
            explicit_streams=explicit_streams,
            aggregate_revenue=self._first_number(facts, AGGREGATE_REVENUE_PATHS),
        )

        covenant_trigger_dscr = self._first_number(facts, COVENANT_TRIGGER_PATHS) or 1.35
        debt_service_annual, debt_service_note = self._infer_debt_service(
            project=project,
            facts=facts,
            base_streams=base_streams,
            covenant_trigger_dscr=covenant_trigger_dscr,
        )

        data_quality_notes = [*current_notes, *base_notes, *full_notes]
        if debt_service_note:
            data_quality_notes.append(debt_service_note)

        base_reference_dscr = (
            self._first_number(facts, DSCR_BASE_PATHS) or self._safe_divide(
                self._scenario_total(base_streams),
                debt_service_annual,
            )
        )
        base_stress_dscr = self._first_number(facts, DSCR_STRESS_PATHS)
        base_resilience = self._resilience_share(base_streams)
        stress_factor_base = self._derive_stress_factor(
            base_reference_dscr=base_reference_dscr,
            base_stress_dscr=base_stress_dscr,
            base_resilience=base_resilience,
        )

        scenario_notes = {
            "current_state": current_notes,
            "base_case": base_notes,
            "full_diversification": full_notes,
        }
        scenario_streams = {
            "current_state": current_streams,
            "base_case": base_streams,
            "full_diversification": full_streams,
        }

        revenue_scenarios = [
            self._build_scenario_mix(
                template=template,
                streams=scenario_streams[template.scenario_id],
                debt_service_annual=debt_service_annual,
                covenant_trigger_dscr=covenant_trigger_dscr,
                stress_factor_base=stress_factor_base,
                base_resilience=base_resilience,
                assumptions=scenario_notes[template.scenario_id],
            )
            for template in SCENARIO_TEMPLATES
        ]

        return RevenueDiversificationVisualizationResponse(
            generated_at=datetime.now(UTC),
            project_id=project_id,
            project_name=project.name,
            debt_service_annual=round(debt_service_annual, 2),
            covenant_trigger_dscr=round(covenant_trigger_dscr, 3),
            non_diesel_combined_coverage_dscr=None,
            non_diesel_senior_coverage_dscr=None,
            stream_definitions=[
                RevenueStreamDefinition(
                    stream_id=STREAMS_BY_ID[stream_id].stream_id,
                    label=STREAMS_BY_ID[stream_id].label,
                    color=STREAMS_BY_ID[stream_id].color,
                    stability_class=STREAMS_BY_ID[stream_id].stability_class,
                    description=STREAMS_BY_ID[stream_id].description,
                )
                for stream_id in STREAM_DEFINITION_ORDER
            ],
            revenue_scenarios=revenue_scenarios,
            risk_proof=None,
            data_quality_notes=self._dedupe_notes(data_quality_notes),
        )

    @staticmethod
    def _matches_caldor_packet(project: Project) -> bool:
        return "caldor" in (project.name or "").casefold()

    def _build_caldor_packet_visualization(
        self,
        *,
        project_id: UUID,
        project: Project,
    ) -> RevenueDiversificationVisualizationResponse:
        return RevenueDiversificationVisualizationResponse(
            generated_at=datetime.now(UTC),
            project_id=project_id,
            project_name=project.name,
            debt_service_annual=3_661_000.0,
            covenant_trigger_dscr=1.35,
            non_diesel_combined_coverage_dscr=1.84,
            non_diesel_senior_coverage_dscr=4.32,
            stream_definitions=[
                RevenueStreamDefinition(
                    stream_id=STREAMS_BY_ID[stream_id].stream_id,
                    label=STREAMS_BY_ID[stream_id].label,
                    color=STREAMS_BY_ID[stream_id].color,
                    stability_class=STREAMS_BY_ID[stream_id].stability_class,
                    description=STREAMS_BY_ID[stream_id].description,
                )
                for stream_id in STREAM_DEFINITION_ORDER
            ],
            revenue_scenarios=[
                self._build_packet_scenario_mix(override) for override in CALDOR_PACKET_SCENARIOS
            ],
            risk_proof=CALDOR_PACKET_RISK_PROOF,
            data_quality_notes=[
                "Visualization aligned to the March 12, 2026 UCS Caldor internal deal packet so the packet's diversification impact is reflected during design review.",
                "Offtake diversification in the packet remains template-stage; this view is packet-modeled rather than workflow-derived from executed agreements.",
            ],
        )

    def _build_packet_scenario_mix(
        self,
        override: _PacketScenarioOverride,
    ) -> RevenueScenarioMix:
        streams = {
            stream_id: _StreamAmount(
                amount=amount,
                source_path="packet.ucs_caldor_2026_internal_deal_packet",
                is_inferred=stream_id in override.inferred_streams,
            )
            for stream_id, amount in override.streams.items()
        }
        total_revenue = self._scenario_total(streams)

        return RevenueScenarioMix(
            scenario_id=override.scenario_id,
            label=override.label,
            total_revenue=round(total_revenue, 2),
            revenue_streams=self._stream_slices(streams, total_revenue),
            dscr_mean=override.dscr_mean,
            dscr_minimum=override.dscr_minimum,
            breach_weeks=override.breach_weeks,
            implied_rating=override.implied_rating,
            breakeven_diesel_price=override.breakeven_diesel_price,
            dscr_parity_diesel_price=override.dscr_parity_diesel_price,
            covenant_trigger_diesel_price=override.covenant_trigger_diesel_price,
            safety_status=override.safety_status,
            safety_label=override.safety_label,
            assumptions=list(override.assumptions),
        )

    async def _list_preferred_facts(
        self,
        project_id: UUID,
    ) -> dict[str, ExtractedFact]:
        schema_paths = list(AGGREGATE_REVENUE_PATHS) + list(DSCR_BASE_PATHS) + list(
            DSCR_STRESS_PATHS
        ) + list(COVENANT_TRIGGER_PATHS)
        for stream in STREAM_REGISTRY:
            schema_paths.extend(stream.schema_paths)

        result = await self.db.execute(
            select(ExtractedFact).where(
                and_(
                    ExtractedFact.project_id == str(project_id),
                    ExtractedFact.schema_path.in_(schema_paths),
                    ExtractedFact.review_status == ReviewStatus.APPROVED.value,
                    ExtractedFact.lifecycle_state != "archived",
                )
            )
        )
        facts = list(result.scalars().all())
        return FactService.select_preferred_facts_by_path(facts)

    def _extract_explicit_streams(
        self,
        facts: Mapping[str, ExtractedFact],
    ) -> dict[str, _StreamAmount]:
        out: dict[str, _StreamAmount] = {}
        for stream in STREAM_REGISTRY:
            for schema_path in stream.schema_paths:
                fact = facts.get(schema_path)
                if not fact:
                    continue
                amount = self._coerce_number(fact.value)
                if amount is None or amount <= 0:
                    continue
                out[stream.stream_id] = _StreamAmount(
                    amount=float(amount),
                    source_path=schema_path,
                    is_inferred=False,
                )
                break
        return out

    def _build_current_streams(
        self,
        *,
        explicit_streams: Mapping[str, _StreamAmount],
        aggregate_revenue: float | None,
    ) -> tuple[dict[str, _StreamAmount], list[str]]:
        notes: list[str] = []
        current: dict[str, _StreamAmount] = {}

        for stream_id in ("diesel", "biochar"):
            stream = explicit_streams.get(stream_id)
            if not stream or stream.amount <= 0:
                continue
            current[stream_id] = _StreamAmount(
                amount=stream.amount,
                source_path=stream.source_path,
                is_inferred=False,
            )

        if not current and aggregate_revenue and aggregate_revenue > 0:
            current["diesel"] = _StreamAmount(
                amount=float(aggregate_revenue),
                source_path=AGGREGATE_REVENUE_PATHS[0],
                is_inferred=True,
            )
            notes.append(
                "Current-state revenue defaulted to diesel concentration because only aggregate revenue evidence was available."
            )

        return current, notes

    def _build_future_streams(
        self,
        *,
        template: _ScenarioTemplate,
        starting_streams: Mapping[str, _StreamAmount],
        explicit_streams: Mapping[str, _StreamAmount],
        aggregate_revenue: float | None,
    ) -> tuple[dict[str, _StreamAmount], list[str]]:
        streams = self._copy_streams(starting_streams)
        notes: list[str] = []

        for stream_id, stream in explicit_streams.items():
            registry = STREAMS_BY_ID[stream_id]
            if STAGE_ORDER[registry.activation_stage] > STAGE_ORDER[template.activation_stage]:
                continue
            existing = streams.get(stream_id)
            if existing and existing.amount >= stream.amount:
                continue
            streams[stream_id] = _StreamAmount(
                amount=stream.amount,
                source_path=stream.source_path,
                is_inferred=False,
            )

        current_total = self._scenario_total(streams)
        diesel_amount = streams.get("diesel", _StreamAmount(0.0)).amount
        target_total = current_total
        if aggregate_revenue and aggregate_revenue > 0:
            target_total = max(target_total, float(aggregate_revenue))
        if template.target_diesel_share and diesel_amount > 0:
            target_total = max(target_total, diesel_amount / template.target_diesel_share)

        inferred_gap = max(0.0, target_total - self._scenario_total(streams))
        if inferred_gap > 0.5:
            self._apply_inferred_gap(
                streams=streams,
                weights=template.inferred_weights,
                activated_stage=template.activation_stage,
                inferred_gap=inferred_gap,
            )
            notes.append(
                f"{template.label} includes inferred revenue mix uplifts because explicit future-stream facts were incomplete."
            )

        return streams, notes

    def _apply_inferred_gap(
        self,
        *,
        streams: dict[str, _StreamAmount],
        weights: Mapping[str, float],
        activated_stage: str,
        inferred_gap: float,
    ) -> None:
        candidates = [
            stream_id
            for stream_id, weight in weights.items()
            if weight > 0 and STAGE_ORDER[STREAMS_BY_ID[stream_id].activation_stage] <= STAGE_ORDER[activated_stage]
        ]
        if not candidates:
            return

        missing_candidates = [stream_id for stream_id in candidates if stream_id not in streams]
        allocation_targets = missing_candidates or candidates
        weight_total = sum(weights[stream_id] for stream_id in allocation_targets)
        if weight_total <= 0:
            return

        for stream_id in allocation_targets:
            allocation = inferred_gap * (weights[stream_id] / weight_total)
            if allocation <= 0:
                continue
            existing = streams.get(stream_id)
            if existing:
                existing.amount += allocation
                existing.is_inferred = existing.is_inferred or existing.source_path is None
            else:
                streams[stream_id] = _StreamAmount(
                    amount=allocation,
                    source_path=None,
                    is_inferred=True,
                )

    def _infer_debt_service(
        self,
        *,
        project: Project,
        facts: Mapping[str, ExtractedFact],
        base_streams: Mapping[str, _StreamAmount],
        covenant_trigger_dscr: float,
    ) -> tuple[float, str | None]:
        base_total = self._scenario_total(base_streams)
        dscr_base = self._first_number(facts, DSCR_BASE_PATHS)

        if dscr_base and dscr_base > 0 and base_total > 0:
            return base_total / dscr_base, (
                "Debt service line derived from approved base-case DSCR evidence and assembled scenario revenue."
            )

        if project.target_bond_amount and project.target_bond_amount > 0:
            return float(project.target_bond_amount) * 0.0725, (
                "Debt service line inferred from target bond amount because explicit DSCR evidence was unavailable."
            )

        fallback_dscr = max(covenant_trigger_dscr + 0.35, 1.75)
        reference_total = max(base_total, 1.0)
        return reference_total / fallback_dscr, (
            "Debt service line inferred from assembled revenue because explicit debt-service evidence was unavailable."
        )

    def _build_scenario_mix(
        self,
        *,
        template: _ScenarioTemplate,
        streams: Mapping[str, _StreamAmount],
        debt_service_annual: float,
        covenant_trigger_dscr: float,
        stress_factor_base: float,
        base_resilience: float,
        assumptions: list[str],
    ) -> RevenueScenarioMix:
        total_revenue = self._scenario_total(streams)
        diesel_amount = streams.get("diesel", _StreamAmount(0.0)).amount
        diesel_share = self._safe_divide(diesel_amount, total_revenue)
        resilience_share = self._resilience_share(streams)
        dscr_mean = self._safe_divide(total_revenue, debt_service_annual)
        stress_factor = max(
            0.45,
            min(0.97, stress_factor_base + max(0.0, resilience_share - base_resilience) * 0.35),
        )
        if template.scenario_id == "current_state":
            stress_factor = max(0.45, stress_factor - max(0.0, base_resilience - resilience_share) * 0.12)

        dscr_minimum = dscr_mean * stress_factor
        breach_weeks = self._breach_weeks(
            dscr_minimum=dscr_minimum,
            covenant_trigger_dscr=covenant_trigger_dscr,
            resilience_share=resilience_share,
        )
        implied_rating = self._implied_rating(
            dscr_minimum=dscr_minimum,
            covenant_trigger_dscr=covenant_trigger_dscr,
        )
        breakeven_price = self._diesel_price_threshold(
            dscr_target=1.0,
            dscr_mean=dscr_mean,
            diesel_share=diesel_share,
            resilience_share=resilience_share,
        )
        covenant_trigger_price = self._diesel_price_threshold(
            dscr_target=covenant_trigger_dscr,
            dscr_mean=dscr_mean,
            diesel_share=diesel_share,
            resilience_share=resilience_share,
        )
        safety_status, safety_label = self._safety_status(
            breach_weeks=breach_weeks,
            dscr_mean=dscr_mean,
            dscr_minimum=dscr_minimum,
            covenant_trigger_dscr=covenant_trigger_dscr,
            resilience_share=resilience_share,
        )

        return RevenueScenarioMix(
            scenario_id=template.scenario_id,
            label=template.label,
            total_revenue=round(total_revenue, 2),
            revenue_streams=self._stream_slices(streams, total_revenue),
            dscr_mean=round(dscr_mean, 2),
            dscr_minimum=round(dscr_minimum, 2),
            breach_weeks=breach_weeks,
            implied_rating=implied_rating,
            breakeven_diesel_price=round(breakeven_price, 2),
            dscr_parity_diesel_price=None,
            covenant_trigger_diesel_price=round(covenant_trigger_price, 2),
            safety_status=safety_status,
            safety_label=safety_label,
            assumptions=self._dedupe_notes(assumptions),
        )

    def _stream_slices(
        self,
        streams: Mapping[str, _StreamAmount],
        total_revenue: float,
    ) -> list[RevenueStreamSlice]:
        slices: list[RevenueStreamSlice] = []
        for stream_id in STREAM_RENDER_ORDER:
            amount = streams.get(stream_id)
            if not amount or amount.amount <= 0:
                continue
            registry = STREAMS_BY_ID[stream_id]
            slices.append(
                RevenueStreamSlice(
                    stream_id=stream_id,
                    label=registry.label,
                    amount=round(amount.amount, 2),
                    pct_of_total=round(self._safe_divide(amount.amount, total_revenue), 4),
                    color=registry.color,
                    stability_class=registry.stability_class,
                    is_inferred=amount.is_inferred,
                    source_path=amount.source_path,
                )
            )
        return slices

    @staticmethod
    def _copy_streams(streams: Mapping[str, _StreamAmount]) -> dict[str, _StreamAmount]:
        return {
            stream_id: _StreamAmount(
                amount=value.amount,
                source_path=value.source_path,
                is_inferred=value.is_inferred,
            )
            for stream_id, value in streams.items()
        }

    @staticmethod
    def _scenario_total(streams: Mapping[str, _StreamAmount]) -> float:
        return float(sum(max(0.0, value.amount) for value in streams.values()))

    @staticmethod
    def _resilience_share(streams: Mapping[str, _StreamAmount]) -> float:
        total = sum(max(0.0, value.amount) for value in streams.values())
        if total <= 0:
            return 0.0

        resilient = 0.0
        for stream_id, value in streams.items():
            registry = STREAMS_BY_ID.get(stream_id)
            if not registry:
                continue
            if registry.stability_class == RevenueStabilityClass.STABLE:
                resilient += value.amount
            elif registry.stability_class == RevenueStabilityClass.BALANCED:
                resilient += value.amount * 0.60
        return resilient / total

    def _derive_stress_factor(
        self,
        *,
        base_reference_dscr: float,
        base_stress_dscr: float | None,
        base_resilience: float,
    ) -> float:
        if base_reference_dscr > 0 and base_stress_dscr and base_stress_dscr > 0:
            return min(0.97, max(0.45, base_stress_dscr / base_reference_dscr))
        return min(0.97, max(0.60, 0.72 + (base_resilience * 0.18)))

    @staticmethod
    def _breach_weeks(
        *,
        dscr_minimum: float,
        covenant_trigger_dscr: float,
        resilience_share: float,
    ) -> int:
        if covenant_trigger_dscr <= 0 or dscr_minimum >= covenant_trigger_dscr:
            return 0
        shortfall_ratio = (covenant_trigger_dscr - dscr_minimum) / covenant_trigger_dscr
        volatility_penalty = 1.7 - min(resilience_share, 0.80)
        return min(312, max(1, ceil(312 * shortfall_ratio * volatility_penalty)))

    @staticmethod
    def _implied_rating(
        *,
        dscr_minimum: float,
        covenant_trigger_dscr: float,
    ) -> str:
        if dscr_minimum >= 3.0:
            return "AAA"
        if dscr_minimum >= 2.25:
            return "AA"
        if dscr_minimum >= 1.75:
            return "A"
        if dscr_minimum >= covenant_trigger_dscr:
            return "BBB"
        return "BB"

    @staticmethod
    def _diesel_price_threshold(
        *,
        dscr_target: float,
        dscr_mean: float,
        diesel_share: float,
        resilience_share: float,
    ) -> float:
        effective_dscr = max(dscr_mean, 0.20)
        dependency_factor = max(0.20, 0.60 + diesel_share - (resilience_share * 0.35))
        return max(
            0.20,
            REFERENCE_DIESEL_PRICE * (dscr_target / effective_dscr) * dependency_factor,
        )

    @staticmethod
    def _safety_status(
        *,
        breach_weeks: int,
        dscr_mean: float,
        dscr_minimum: float,
        covenant_trigger_dscr: float,
        resilience_share: float,
    ) -> tuple[RevenueScenarioSafety, str]:
        if breach_weeks > 0 or dscr_minimum < covenant_trigger_dscr:
            return RevenueScenarioSafety.FRAGILE, "Razor-thin"
        if dscr_mean >= 2.5 and resilience_share >= 0.30:
            return RevenueScenarioSafety.FORTRESS, "Fortress"
        return RevenueScenarioSafety.SAFE, "Safe"

    @staticmethod
    def _safe_divide(numerator: float | None, denominator: float | None) -> float:
        if numerator is None or denominator is None or denominator == 0:
            return 0.0
        return float(numerator) / float(denominator)

    @staticmethod
    def _dedupe_notes(notes: list[str]) -> list[str]:
        seen: set[str] = set()
        ordered: list[str] = []
        for note in notes:
            normalized = note.strip()
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            ordered.append(normalized)
        return ordered

    def _first_number(
        self,
        facts: Mapping[str, ExtractedFact],
        schema_paths: tuple[str, ...],
    ) -> float | None:
        for schema_path in schema_paths:
            fact = facts.get(schema_path)
            if not fact:
                continue
            number = self._coerce_number(fact.value)
            if number is None:
                continue
            return float(number)
        return None

    @classmethod
    def _coerce_number(cls, value: object) -> float | None:
        if value is None:
            return None

        if isinstance(value, bool):
            return float(value)

        if isinstance(value, int | float):
            return float(value)

        if isinstance(value, str):
            normalized = value.strip().replace(",", "").replace("$", "")
            if not normalized:
                return None
            try:
                return float(normalized)
            except ValueError:
                return None

        if isinstance(value, Mapping):
            for key in ("value", "amount", "annual", "total", "usd"):
                if key in value:
                    nested = cls._coerce_number(value[key])
                    if nested is not None:
                        return nested
            return None

        if isinstance(value, list) and len(value) == 1:
            return cls._coerce_number(value[0])

        return None
