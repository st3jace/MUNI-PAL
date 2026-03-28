"""
Template and clause services for the document management system.

Implements Phase 2 backend functionality:
- Template CRUD
- Jinja2 rendering to TipTap JSON
- Clause library CRUD
- Deal-structure-driven clause recommendations
"""

from __future__ import annotations

import json
from uuid import UUID

from jinja2 import Environment, StrictUndefined, meta
from jinja2.sandbox import SandboxedEnvironment
from sqlalchemy import String, cast, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from munipal.core.models.deal_document import (
    DealDocumentType,
    DocumentTemplate,
    TemplateClause,
)
from munipal.core.schemas.deal_document import (
    ClauseCreate,
    ClauseRead,
    ClauseRecommendation,
    ClauseRecommendationRequest,
    ClauseUpdate,
    DealDocumentTypeRead,
    DealVertical,
    DocumentCategory,
    RetentionPolicy,
    TemplateCreate,
    TemplateRead,
    TemplateRenderRequest,
    TemplateRenderResult,
    TemplateSummary,
    TemplateUpdate,
)
from munipal.services.legal_corpus_service import LegalCorpusService

FEATURE_TO_CLAUSE_CATEGORIES: dict[str, set[str]] = {
    "additional_bonds_test": {"additional_bonds_test", "covenant"},
    "debt_service_reserve_fund": {"reserve_fund", "flow_of_funds", "covenant"},
    "rate_covenant": {"rate_covenant", "covenant"},
    "flow_of_funds": {"flow_of_funds"},
    "event_of_default": {"default_events", "events_of_default"},
    "cross_default": {"default_events", "events_of_default"},
    "tip_fee": {"revenue_contracts", "project_agreements"},
    "power_purchase": {"revenue_contracts", "project_agreements"},
    "interconnection": {"project_agreements", "utility_provisions"},
    "environmental_permit": {"regulatory", "project_agreements"},
    "continuing_disclosure": {"disclosure", "regulatory"},
    "waterfall": {"distribution_waterfall", "economics"},
    "lpa_waterfall": {"distribution_waterfall", "economics"},
    "clawback": {"distribution_waterfall", "economics"},
    "side_letter": {"investor_terms"},
    "subscription": {"investor_onboarding"},
    "official_statement": {"disclosure"},
}


DOC_TYPE_CODE_TO_CLAUSE_CATEGORIES: dict[str, set[str]] = {
    "trust_indenture": {"rate_covenant", "additional_bonds_test", "default_events", "flow_of_funds"},
    "loan_agreement": {"rate_covenant", "default_events", "covenant"},
    "bond_purchase_agreement": {"representations", "conditions_precedent"},
    "letter_of_credit": {"credit_enhancement", "default_events", "covenant"},
    "continuing_disclosure_agreement": {"disclosure", "regulatory"},
    "tax_certificate": {"tax_compliance", "regulatory"},
    "nda": {"confidentiality"},
    "official_statement": {"disclosure", "risk_factors"},
}


class TemplateService:
    """Service for templates, clause library, and recommendation workflows."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._legal_corpus = LegalCorpusService()

    # ------------------------------------------------------------------
    # Template CRUD
    # ------------------------------------------------------------------

    async def create_template(
        self,
        data: TemplateCreate,
        *,
        tenant_id: str = "default",
    ) -> TemplateRead:
        """Create a new template and auto-increment version by name/type/jurisdiction."""
        document_type = await self.db.get(DealDocumentType, str(data.document_type_id))
        if not document_type:
            raise ValueError(f"Document type {data.document_type_id} not found")

        version_query = (
            select(func.max(DocumentTemplate.version))
            .where(
                DocumentTemplate.name == data.name,
                DocumentTemplate.document_type_id == str(data.document_type_id),
                DocumentTemplate.tenant_id == tenant_id,
                DocumentTemplate.jurisdiction == data.jurisdiction,
            )
        )
        max_version = (await self.db.execute(version_query)).scalar() or 0

        template = DocumentTemplate(
            name=data.name,
            document_type_id=str(data.document_type_id),
            jurisdiction=data.jurisdiction,
            version=max_version + 1,
            template_body=data.template_body,
            variable_schema=data.variable_schema or {},
            is_active=True,
            is_system=False,
            tenant_id=tenant_id,
        )
        self.db.add(template)
        await self.db.flush()
        await self.db.refresh(template)

        return self._template_to_read(template, document_type)

    async def get_template(
        self,
        template_id: UUID,
    ) -> TemplateRead | None:
        """Get a template by ID."""
        template = await self.db.get(DocumentTemplate, str(template_id))
        if not template:
            return None

        document_type = await self.db.get(DealDocumentType, template.document_type_id)
        return self._template_to_read(template, document_type)

    async def list_templates(
        self,
        *,
        tenant_id: str = "default",
        document_type_id: UUID | None = None,
        jurisdiction: str | None = None,
        active_only: bool = True,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[TemplateSummary], int]:
        """List templates with filters and pagination."""
        base = select(DocumentTemplate).where(DocumentTemplate.tenant_id == tenant_id)
        count_q = select(func.count(DocumentTemplate.id)).where(
            DocumentTemplate.tenant_id == tenant_id
        )

        if document_type_id:
            base = base.where(DocumentTemplate.document_type_id == str(document_type_id))
            count_q = count_q.where(DocumentTemplate.document_type_id == str(document_type_id))
        if jurisdiction:
            base = base.where(DocumentTemplate.jurisdiction == jurisdiction)
            count_q = count_q.where(DocumentTemplate.jurisdiction == jurisdiction)
        if active_only:
            base = base.where(DocumentTemplate.is_active.is_(True))
            count_q = count_q.where(DocumentTemplate.is_active.is_(True))

        total = (await self.db.execute(count_q)).scalar() or 0
        result = await self.db.execute(
            base.order_by(DocumentTemplate.updated_at.desc()).offset(skip).limit(limit)
        )
        templates = result.scalars().all()

        summaries: list[TemplateSummary] = []
        for template in templates:
            document_type = await self.db.get(DealDocumentType, template.document_type_id)
            summaries.append(
                TemplateSummary(
                    id=UUID(template.id),
                    name=template.name,
                    document_type_id=UUID(template.document_type_id),
                    document_type_code=document_type.code if document_type else None,
                    jurisdiction=template.jurisdiction,
                    version=template.version,
                    is_active=template.is_active,
                    is_system=template.is_system,
                    updated_at=template.updated_at,
                )
            )
        return summaries, total

    async def update_template(
        self,
        template_id: UUID,
        data: TemplateUpdate,
    ) -> TemplateRead | None:
        """Update template metadata/content and bump version if body/schema changed."""
        template = await self.db.get(DocumentTemplate, str(template_id))
        if not template:
            return None

        update_data = data.model_dump(exclude_unset=True)
        body_changed = False

        for field, value in update_data.items():
            if field in {"template_body", "variable_schema"}:
                current = getattr(template, field)
                if current != value:
                    body_changed = True
            setattr(template, field, value)

        if body_changed:
            template.version = int(template.version or 1) + 1

        await self.db.flush()
        await self.db.refresh(template)

        document_type = await self.db.get(DealDocumentType, template.document_type_id)
        return self._template_to_read(template, document_type)

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    async def render_template(
        self,
        template_id: UUID,
        data: TemplateRenderRequest,
    ) -> TemplateRenderResult:
        """Render a template and return TipTap-compatible JSON output."""
        template = await self.db.get(DocumentTemplate, str(template_id))
        if not template:
            raise ValueError(f"Template {template_id} not found")

        used_variables = self._extract_template_variables(template.template_body)
        provided_keys = set(data.variables.keys())
        missing_variables = sorted(var for var in used_variables if var not in provided_keys)
        if missing_variables:
            missing = ", ".join(missing_variables)
            raise ValueError(f"Missing template variables: {missing}")
        warnings: list[str] = []

        env = SandboxedEnvironment(undefined=StrictUndefined, autoescape=False)
        try:
            rendered_text = env.from_string(template.template_body).render(**data.variables)
        except Exception as exc:  # noqa: BLE001
            raise ValueError(f"Template render failed: {exc}") from exc

        content_json = self._to_tiptap_json(rendered_text)
        return TemplateRenderResult(
            template_id=template_id,
            content_json=content_json,
            rendered_text=rendered_text,
            missing_variables=missing_variables,
            used_variables=used_variables,
            warnings=warnings,
        )

    @staticmethod
    def _extract_template_variables(template_body: str) -> list[str]:
        env = Environment()
        parsed = env.parse(template_body)
        return sorted(meta.find_undeclared_variables(parsed))

    @staticmethod
    def _to_tiptap_json(rendered_text: str) -> dict | None:
        stripped = rendered_text.strip()
        if not stripped:
            return None

        # If template already renders TipTap/ProseMirror JSON, preserve it.
        try:
            parsed = json.loads(stripped)
            if isinstance(parsed, dict):
                return parsed
        except Exception:  # noqa: BLE001
            pass

        paragraphs = []
        for line in stripped.splitlines():
            text = line.strip()
            if not text:
                continue
            paragraphs.append(
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": text}],
                }
            )
        if not paragraphs:
            paragraphs = [
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": stripped}],
                }
            ]
        return {"type": "doc", "content": paragraphs}

    # ------------------------------------------------------------------
    # Clause CRUD
    # ------------------------------------------------------------------

    async def create_clause(
        self,
        data: ClauseCreate,
        *,
        tenant_id: str = "default",
    ) -> ClauseRead:
        """Create a clause entry for the reusable clause library."""
        if data.template_id:
            template = await self.db.get(DocumentTemplate, str(data.template_id))
            if not template:
                raise ValueError(f"Template {data.template_id} not found")

        clause = TemplateClause(
            template_id=str(data.template_id) if data.template_id else None,
            name=data.name,
            category=data.category,
            content_json=data.content_json,
            description=data.description,
            jurisdiction=data.jurisdiction,
            is_active=True,
            tenant_id=tenant_id,
        )
        self.db.add(clause)
        await self.db.flush()
        await self.db.refresh(clause)
        return self._clause_to_read(clause)

    async def get_clause(self, clause_id: UUID) -> ClauseRead | None:
        clause = await self.db.get(TemplateClause, str(clause_id))
        if not clause:
            return None
        return self._clause_to_read(clause)

    async def update_clause(
        self,
        clause_id: UUID,
        data: ClauseUpdate,
    ) -> ClauseRead | None:
        clause = await self.db.get(TemplateClause, str(clause_id))
        if not clause:
            return None

        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(clause, field, value)

        await self.db.flush()
        await self.db.refresh(clause)
        return self._clause_to_read(clause)

    async def list_clauses(
        self,
        *,
        tenant_id: str = "default",
        template_id: UUID | None = None,
        category: str | None = None,
        jurisdiction: str | None = None,
        text_query: str | None = None,
        active_only: bool = True,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[ClauseRead], int]:
        """List clause entries with filters and text search."""
        base = select(TemplateClause).where(TemplateClause.tenant_id == tenant_id)
        count_q = select(func.count(TemplateClause.id)).where(TemplateClause.tenant_id == tenant_id)

        if template_id:
            base = base.where(TemplateClause.template_id == str(template_id))
            count_q = count_q.where(TemplateClause.template_id == str(template_id))
        if category:
            base = base.where(TemplateClause.category == category)
            count_q = count_q.where(TemplateClause.category == category)
        if jurisdiction:
            base = base.where(TemplateClause.jurisdiction == jurisdiction)
            count_q = count_q.where(TemplateClause.jurisdiction == jurisdiction)
        if active_only:
            base = base.where(TemplateClause.is_active.is_(True))
            count_q = count_q.where(TemplateClause.is_active.is_(True))
        if text_query:
            pattern = f"%{text_query.strip()}%"
            query_filter = or_(
                TemplateClause.name.ilike(pattern),
                TemplateClause.description.ilike(pattern),
                cast(TemplateClause.content_json, String).ilike(pattern),
            )
            base = base.where(query_filter)
            count_q = count_q.where(query_filter)

        total = (await self.db.execute(count_q)).scalar() or 0
        result = await self.db.execute(
            base.order_by(TemplateClause.updated_at.desc()).offset(skip).limit(limit)
        )
        clauses = result.scalars().all()
        return [self._clause_to_read(clause) for clause in clauses], total

    # ------------------------------------------------------------------
    # Clause Recommendations
    # ------------------------------------------------------------------

    async def recommend_clauses(
        self,
        request: ClauseRecommendationRequest,
        *,
        tenant_id: str = "default",
    ) -> list[ClauseRecommendation]:
        """Recommend clauses based on document type, features, and text intent."""
        library_clauses, _ = await self.list_clauses(
            tenant_id=tenant_id,
            jurisdiction=request.jurisdiction,
            text_query=request.text_query,
            active_only=True,
            skip=0,
            limit=500,
        )

        feature_tokens = self._normalize_feature_tokens(request.deal_features)
        preferred_categories = self._preferred_categories(
            request.document_type_code,
            feature_tokens,
        )
        query_tokens = self._tokenize_text(request.text_query or "")

        recommendations: list[ClauseRecommendation] = []
        for clause in library_clauses:
            score = 0.0
            reason_parts: list[str] = []

            blob = self._clause_text_blob(clause)

            if request.jurisdiction and clause.jurisdiction == request.jurisdiction:
                score += 1.0
                reason_parts.append("jurisdiction_match")

            if clause.category.strip().lower() in preferred_categories:
                score += 2.0
                reason_parts.append("category_match")

            for feature in feature_tokens:
                if feature in blob:
                    score += 1.5
                    reason_parts.append(f"feature_text:{feature}")

            for token in query_tokens:
                if token in blob:
                    score += 0.35

            if score <= 0:
                continue

            recommendations.append(
                ClauseRecommendation(
                    clause_id=clause.id,
                    clause_name=clause.name,
                    category=clause.category,
                    score=round(score, 3),
                    reason=", ".join(sorted(set(reason_parts))) or "score_match",
                    source="library",
                    sample_documents=[],
                )
            )

        recommendations.sort(key=lambda item: item.score, reverse=True)
        recommendations = recommendations[: request.limit]

        if len(recommendations) < request.limit and self._legal_corpus.has_catalog():
            remaining = request.limit - len(recommendations)
            corpus_items = self._legal_corpus.recommend_document_classes(
                document_type_code=request.document_type_code,
                deal_features=request.deal_features,
                limit=remaining + 5,
            )
            for item in corpus_items:
                name = self._title_from_slug(item.get("class_name", "legal_template"))
                if any(r.clause_name == name for r in recommendations):
                    continue
                recommendations.append(
                    ClauseRecommendation(
                        clause_id=None,
                        clause_name=name,
                        category=self._corpus_category(item.get("class_name", "")),
                        score=float(item.get("score", 0.0)),
                        reason=", ".join(item.get("reasons", [])) or "corpus_match",
                        source="catalog",
                        sample_documents=item.get("sample_files", [])[:5],
                    )
                )
                if len(recommendations) >= request.limit:
                    break

        return recommendations[: request.limit]

    @staticmethod
    def _corpus_category(class_name: str) -> str:
        value = class_name.strip().lower()
        if "official_statement" in value or "disclosure" in value:
            return "disclosure"
        if "indenture" in value or "agreement" in value:
            return "negotiated"
        if "permit" in value or "notice" in value:
            return "regulatory"
        return "templated"

    @staticmethod
    def _title_from_slug(slug: str) -> str:
        parts = [p for p in slug.replace("-", "_").split("_") if p]
        return " ".join(part.capitalize() for part in parts) or "Legal Template"

    @staticmethod
    def _normalize_feature_tokens(values: list[str]) -> list[str]:
        normalized: list[str] = []
        seen: set[str] = set()
        for raw in values:
            if not isinstance(raw, str):
                continue
            value = raw.strip().lower()
            if not value:
                continue
            value = value.replace("-", "_").replace(" ", "_")
            if value in seen:
                continue
            seen.add(value)
            normalized.append(value)
        return normalized

    @staticmethod
    def _tokenize_text(text: str) -> list[str]:
        tokens = []
        for token in text.lower().split():
            stripped = "".join(ch for ch in token if ch.isalnum() or ch == "_")
            if len(stripped) >= 3:
                tokens.append(stripped)
        return list(dict.fromkeys(tokens))

    @staticmethod
    def _clause_text_blob(clause: ClauseRead) -> str:
        parts = [clause.name, clause.category, clause.description or ""]
        try:
            parts.append(json.dumps(clause.content_json, sort_keys=True))
        except Exception:  # noqa: BLE001
            parts.append("")
        return " ".join(parts).lower()

    @staticmethod
    def _preferred_categories(
        document_type_code: str | None,
        feature_tokens: list[str],
    ) -> set[str]:
        categories: set[str] = set()
        if document_type_code:
            code = document_type_code.strip().lower()
            categories.update(DOC_TYPE_CODE_TO_CLAUSE_CATEGORIES.get(code, set()))
        for token in feature_tokens:
            categories.update(FEATURE_TO_CLAUSE_CATEGORIES.get(token, set()))
        return {category.strip().lower() for category in categories}

    # ------------------------------------------------------------------
    # Model -> Schema Converters
    # ------------------------------------------------------------------

    @staticmethod
    def _type_to_schema(doc_type: DealDocumentType) -> DealDocumentTypeRead:
        return DealDocumentTypeRead(
            id=UUID(doc_type.id),
            code=doc_type.code,
            display_name=doc_type.display_name,
            category=DocumentCategory(doc_type.category),
            deal_vertical=DealVertical(doc_type.deal_vertical),
            description=doc_type.description,
            default_workflow=doc_type.default_workflow,
            retention_policy=RetentionPolicy(doc_type.retention_policy),
            requires_signature=doc_type.requires_signature,
            is_active=doc_type.is_active,
            sort_order=doc_type.sort_order,
            created_at=doc_type.created_at,
            updated_at=doc_type.updated_at,
        )

    def _template_to_read(
        self,
        template: DocumentTemplate,
        document_type: DealDocumentType | None,
    ) -> TemplateRead:
        return TemplateRead(
            id=UUID(template.id),
            name=template.name,
            document_type_id=UUID(template.document_type_id),
            document_type=(self._type_to_schema(document_type) if document_type else None),
            jurisdiction=template.jurisdiction,
            version=template.version,
            template_body=template.template_body,
            variable_schema=template.variable_schema,
            is_active=template.is_active,
            is_system=template.is_system,
            tenant_id=template.tenant_id,
            created_at=template.created_at,
            updated_at=template.updated_at,
        )

    @staticmethod
    def _clause_to_read(clause: TemplateClause) -> ClauseRead:
        return ClauseRead(
            id=UUID(clause.id),
            template_id=UUID(clause.template_id) if clause.template_id else None,
            name=clause.name,
            category=clause.category,
            content_json=clause.content_json,
            description=clause.description,
            jurisdiction=clause.jurisdiction,
            is_active=clause.is_active,
            tenant_id=clause.tenant_id,
            created_at=clause.created_at,
            updated_at=clause.updated_at,
        )
