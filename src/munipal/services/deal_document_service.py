"""
Deal document service - business logic for document lifecycle management.

Implements the state machine: draft → under_review → approved → execution →
signed → filed → archived. Manages version history, content updates, and
closing checklist generation.
"""

from __future__ import annotations

import hashlib
import json
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from munipal.core.models.deal_document import (
    DealDocument,
    DealDocumentType,
    DealDocumentVersion,
    DocumentReview,
    DocumentTemplate,
)
from munipal.core.schemas.deal_document import (
    ChecklistItemRead,
    ContentUpdateRequest,
    DealDocumentCreate,
    DealDocumentRead,
    DealDocumentSummary,
    DealDocumentTypeRead,
    DealDocumentUpdate,
    DealDocumentVersionRead,
    DocumentCategory,
    DocumentStatus,
    RetentionPolicy,
    SnapshotReason,
    UserSummary,
    VersionDiff,
)
from munipal.services.document_audit_service import DocumentAuditService


# ---------------------------------------------------------------------------
# Valid state transitions
# ---------------------------------------------------------------------------

VALID_TRANSITIONS: dict[str, set[str]] = {
    "draft": {"under_review"},
    "under_review": {"approved", "draft"},
    "approved": {"execution"},
    "execution": {"signed"},
    "signed": {"filed"},
    "filed": {"archived"},
}


class DealDocumentService:
    """Service for deal document CRUD, workflow, and version management."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._audit = DocumentAuditService(db)

    # ------------------------------------------------------------------
    # CREATE
    # ------------------------------------------------------------------

    async def create(
        self,
        data: DealDocumentCreate,
        created_by_id: str,
        tenant_id: str = "default",
    ) -> DealDocumentRead:
        """
        Create a new deal document.

        If template_id is provided, renders the template with variables
        to produce initial content.
        """
        # Validate document type exists
        doc_type = await self.db.get(DealDocumentType, str(data.document_type_id))
        if not doc_type:
            raise ValueError(f"Document type {data.document_type_id} not found")

        # Resolve content from template if specified
        content_json = data.content_json
        template_version = None
        if data.template_id:
            template = await self.db.get(DocumentTemplate, str(data.template_id))
            if not template:
                raise ValueError(f"Template {data.template_id} not found")
            template_version = template.version
            if data.template_variables and not content_json:
                content_json = self._render_template(
                    template.template_body, data.template_variables
                )

        # Generate document number
        doc_number = await self._next_document_number(str(data.project_id))

        document = DealDocument(
            title=data.title,
            document_number=doc_number,
            document_type_id=str(data.document_type_id),
            status="draft",
            content_json=content_json,
            template_id=str(data.template_id) if data.template_id else None,
            template_version=template_version,
            retention_policy=doc_type.retention_policy,
            project_id=str(data.project_id),
            created_by_id=created_by_id,
            assigned_to_id=str(data.assigned_to_id) if data.assigned_to_id else None,
        )

        self.db.add(document)
        await self.db.flush()
        await self.db.refresh(document)

        # Create initial version snapshot if content is present
        if content_json:
            await self._create_version(
                document, created_by_id, SnapshotReason.MANUAL_SAVE
            )

        # Audit
        await self._audit.log(
            document_id=UUID(document.id),
            actor_id=created_by_id,
            action="created",
            details={
                "title": data.title,
                "document_type": doc_type.code,
                "template_id": str(data.template_id) if data.template_id else None,
            },
        )

        return await self._to_read_schema(document)

    # ------------------------------------------------------------------
    # READ
    # ------------------------------------------------------------------

    async def get(self, document_id: UUID) -> DealDocumentRead | None:
        """Get a document by ID with related data."""
        document = await self.db.get(DealDocument, str(document_id))
        if not document:
            return None
        return await self._to_read_schema(document)

    async def list_for_project(
        self,
        project_id: UUID,
        status_filter: str | None = None,
        type_filter: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[DealDocumentSummary], int]:
        """List documents for a project with optional filters."""
        base = select(DealDocument).where(
            DealDocument.project_id == str(project_id)
        )
        count_q = select(func.count(DealDocument.id)).where(
            DealDocument.project_id == str(project_id)
        )

        if status_filter:
            base = base.where(DealDocument.status == status_filter)
            count_q = count_q.where(DealDocument.status == status_filter)
        if type_filter:
            base = base.join(DealDocumentType).where(
                DealDocumentType.code == type_filter
            )
            count_q = count_q.join(DealDocumentType).where(
                DealDocumentType.code == type_filter
            )

        total = (await self.db.execute(count_q)).scalar() or 0

        query = (
            base.options(selectinload(DealDocument.document_type))
            .order_by(DealDocument.updated_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(query)
        documents = result.scalars().all()

        summaries = []
        for doc in documents:
            doc_type = doc.document_type or await self.db.get(
                DealDocumentType, doc.document_type_id
            )
            summaries.append(
                DealDocumentSummary(
                    id=UUID(doc.id),
                    title=doc.title,
                    document_number=doc.document_number,
                    document_type_code=doc_type.code if doc_type else None,
                    document_type_name=doc_type.display_name if doc_type else None,
                    status=DocumentStatus(doc.status),
                    signature_status=doc.signature_status,
                    legal_hold=doc.legal_hold,
                    assigned_to_name=None,  # Populated by route layer if needed
                    updated_at=doc.updated_at,
                )
            )

        return summaries, total

    # ------------------------------------------------------------------
    # UPDATE CONTENT
    # ------------------------------------------------------------------

    async def update_content(
        self,
        document_id: UUID,
        data: ContentUpdateRequest,
        user_id: str,
    ) -> DealDocumentRead:
        """Update document content (editor auto-save)."""
        document = await self.db.get(DealDocument, str(document_id))
        if not document:
            raise ValueError(f"Document {document_id} not found")
        if document.status not in ("draft", "under_review"):
            raise ValueError(
                f"Cannot edit document in '{document.status}' status"
            )

        document.content_json = data.content_json
        # Generate plaintext for full-text search
        document.content_plaintext = self._extract_plaintext(data.content_json)

        if data.auto_snapshot:
            await self._create_version(
                document, user_id, SnapshotReason.AUTO_SAVE
            )

        await self.db.flush()
        await self.db.refresh(document)

        await self._audit.log(
            document_id=document_id,
            actor_id=user_id,
            action="edited",
        )

        return await self._to_read_schema(document)

    # ------------------------------------------------------------------
    # UPDATE METADATA
    # ------------------------------------------------------------------

    async def update(
        self,
        document_id: UUID,
        data: DealDocumentUpdate,
    ) -> DealDocumentRead | None:
        """Update document metadata (title, assignment)."""
        document = await self.db.get(DealDocument, str(document_id))
        if not document:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if field == "assigned_to_id" and value is not None:
                value = str(value)
            setattr(document, field, value)

        await self.db.flush()
        await self.db.refresh(document)
        return await self._to_read_schema(document)

    # ------------------------------------------------------------------
    # STATUS TRANSITIONS
    # ------------------------------------------------------------------

    async def transition_status(
        self,
        document_id: UUID,
        new_status: str,
        user_id: str,
        comment: str | None = None,
    ) -> DealDocumentRead:
        """
        Transition document to a new workflow status.

        Enforces the state machine and pre-conditions for each transition.
        """
        document = await self.db.get(DealDocument, str(document_id))
        if not document:
            raise ValueError(f"Document {document_id} not found")

        current = document.status
        allowed = VALID_TRANSITIONS.get(current, set())

        if new_status not in allowed:
            raise ValueError(
                f"Cannot transition from '{current}' to '{new_status}'. "
                f"Allowed: {allowed}"
            )

        # Pre-condition checks
        if new_status == "under_review":
            if not document.content_json:
                raise ValueError("Cannot submit empty document for review")
            await self._create_version(
                document, user_id, SnapshotReason.PRE_REVIEW
            )

        if new_status == "approved":
            # Check all reviews are completed
            pending = await self._count_pending_reviews(str(document_id))
            if pending > 0:
                raise ValueError(
                    f"{pending} review(s) still pending. "
                    "All reviews must be completed before approval."
                )

        if new_status == "signed":
            # All signers must have signed (checked by webhook handler)
            pass

        if new_status == "archived" and document.legal_hold:
            raise ValueError(
                "Cannot archive document under legal hold"
            )

        old_status = document.status
        document.status = new_status

        await self.db.flush()
        await self.db.refresh(document)

        await self._audit.log(
            document_id=document_id,
            actor_id=user_id,
            action="status_changed",
            details={
                "from": old_status,
                "to": new_status,
                "comment": comment,
            },
        )

        return await self._to_read_schema(document)

    # ------------------------------------------------------------------
    # VERSIONS
    # ------------------------------------------------------------------

    async def create_version_snapshot(
        self,
        document_id: UUID,
        reason: str,
        user_id: str,
        change_summary: str | None = None,
    ) -> DealDocumentVersionRead:
        """Create an explicit version snapshot."""
        document = await self.db.get(DealDocument, str(document_id))
        if not document:
            raise ValueError(f"Document {document_id} not found")

        version = await self._create_version(
            document, user_id, SnapshotReason(reason), change_summary
        )

        await self._audit.log(
            document_id=document_id,
            actor_id=user_id,
            action="version_saved",
            details={
                "version_number": version.version_number,
                "reason": reason,
            },
        )

        return DealDocumentVersionRead(
            id=UUID(version.id),
            document_id=UUID(version.document_id),
            version_number=version.version_number,
            content_hash=version.content_hash,
            change_summary=version.change_summary,
            snapshot_reason=SnapshotReason(version.snapshot_reason),
            created_by_id=UUID(version.created_by_id),
            storage_path=version.storage_path,
            created_at=version.created_at,
            updated_at=version.updated_at,
        )

    async def get_versions(
        self,
        document_id: UUID,
    ) -> list[DealDocumentVersionRead]:
        """Get all version snapshots for a document."""
        query = (
            select(DealDocumentVersion)
            .where(DealDocumentVersion.document_id == str(document_id))
            .order_by(DealDocumentVersion.version_number.desc())
        )
        result = await self.db.execute(query)
        versions = result.scalars().all()

        return [
            DealDocumentVersionRead(
                id=UUID(v.id),
                document_id=UUID(v.document_id),
                version_number=v.version_number,
                content_hash=v.content_hash,
                change_summary=v.change_summary,
                snapshot_reason=SnapshotReason(v.snapshot_reason),
                created_by_id=UUID(v.created_by_id),
                storage_path=v.storage_path,
                created_at=v.created_at,
                updated_at=v.updated_at,
            )
            for v in versions
        ]

    async def compare_versions(
        self,
        document_id: UUID,
        v1: int,
        v2: int,
    ) -> VersionDiff:
        """Compare two version snapshots."""
        query_a = select(DealDocumentVersion).where(
            DealDocumentVersion.document_id == str(document_id),
            DealDocumentVersion.version_number == v1,
        )
        query_b = select(DealDocumentVersion).where(
            DealDocumentVersion.document_id == str(document_id),
            DealDocumentVersion.version_number == v2,
        )

        ver_a = (await self.db.execute(query_a)).scalar_one_or_none()
        ver_b = (await self.db.execute(query_b)).scalar_one_or_none()

        return VersionDiff(
            document_id=document_id,
            version_a=v1,
            version_b=v2,
            content_a=ver_a.content_json if ver_a else None,
            content_b=ver_b.content_json if ver_b else None,
        )

    # ------------------------------------------------------------------
    # LEGAL HOLD
    # ------------------------------------------------------------------

    async def set_legal_hold(
        self,
        document_id: UUID,
        hold: bool,
        user_id: str,
    ) -> DealDocumentRead:
        """Set or release legal hold on a document."""
        document = await self.db.get(DealDocument, str(document_id))
        if not document:
            raise ValueError(f"Document {document_id} not found")

        document.legal_hold = hold
        await self.db.flush()
        await self.db.refresh(document)

        action = "legal_hold_set" if hold else "legal_hold_released"
        await self._audit.log(
            document_id=document_id,
            actor_id=user_id,
            action=action,
        )

        return await self._to_read_schema(document)

    # ------------------------------------------------------------------
    # DELETE
    # ------------------------------------------------------------------

    async def delete(self, document_id: UUID, user_id: str) -> bool:
        """Delete a document. Blocked by legal hold."""
        document = await self.db.get(DealDocument, str(document_id))
        if not document:
            return False
        if document.legal_hold:
            raise ValueError("Cannot delete document under legal hold")

        await self._audit.log(
            document_id=document_id,
            actor_id=user_id,
            action="deleted",
            details={"title": document.title},
        )

        await self.db.delete(document)
        await self.db.flush()
        return True

    # ------------------------------------------------------------------
    # CLOSING CHECKLIST
    # ------------------------------------------------------------------

    async def generate_closing_checklist(
        self,
        project_id: UUID,
    ) -> list[ChecklistItemRead]:
        """
        Auto-generate a closing checklist from the document type registry.

        Compares required document types against existing documents
        for the project.
        """
        # Get all active muni document types
        type_query = (
            select(DealDocumentType)
            .where(
                DealDocumentType.is_active.is_(True),
                DealDocumentType.deal_vertical == "muni",
            )
            .order_by(DealDocumentType.sort_order)
        )
        result = await self.db.execute(type_query)
        doc_types = result.scalars().all()

        # Get existing documents for the project
        doc_query = select(DealDocument).where(
            DealDocument.project_id == str(project_id)
        )
        doc_result = await self.db.execute(doc_query)
        existing_docs = doc_result.scalars().all()

        # Build lookup by document type
        doc_by_type: dict[str, DealDocument] = {}
        for doc in existing_docs:
            doc_by_type[doc.document_type_id] = doc

        items = []
        for dt in doc_types:
            existing = doc_by_type.get(dt.id)
            is_complete = existing is not None and existing.status in (
                "signed", "filed", "archived"
            )

            items.append(
                ChecklistItemRead(
                    document_type_code=dt.code,
                    document_type_name=dt.display_name,
                    category=DocumentCategory(dt.category),
                    requires_signature=dt.requires_signature,
                    document_id=UUID(existing.id) if existing else None,
                    document_status=(
                        DocumentStatus(existing.status) if existing else None
                    ),
                    is_complete=is_complete,
                )
            )

        return items

    # ------------------------------------------------------------------
    # DOCUMENT TYPES
    # ------------------------------------------------------------------

    async def list_document_types(
        self,
        deal_vertical: str | None = None,
        active_only: bool = True,
    ) -> list[DealDocumentTypeRead]:
        """List available document types."""
        query = select(DealDocumentType)
        if deal_vertical:
            query = query.where(DealDocumentType.deal_vertical == deal_vertical)
        if active_only:
            query = query.where(DealDocumentType.is_active.is_(True))
        query = query.order_by(DealDocumentType.sort_order)

        result = await self.db.execute(query)
        types = result.scalars().all()

        return [self._type_to_schema(t) for t in types]

    # ------------------------------------------------------------------
    # PRIVATE HELPERS
    # ------------------------------------------------------------------

    async def _create_version(
        self,
        document: DealDocument,
        user_id: str,
        reason: SnapshotReason,
        change_summary: str | None = None,
    ) -> DealDocumentVersion:
        """Create an immutable version snapshot."""
        # Get next version number
        count_q = select(func.count(DealDocumentVersion.id)).where(
            DealDocumentVersion.document_id == document.id
        )
        count = (await self.db.execute(count_q)).scalar() or 0
        next_version = count + 1

        # Compute content hash
        content_bytes = json.dumps(
            document.content_json or {}, sort_keys=True
        ).encode()
        content_hash = hashlib.sha256(content_bytes).hexdigest()

        version = DealDocumentVersion(
            document_id=document.id,
            version_number=next_version,
            content_json=document.content_json,
            content_hash=content_hash,
            change_summary=change_summary,
            snapshot_reason=reason.value,
            created_by_id=user_id,
        )

        self.db.add(version)
        await self.db.flush()
        await self.db.refresh(version)
        return version

    async def _next_document_number(self, project_id: str) -> str:
        """Generate next sequential document number for a project."""
        count_q = select(func.count(DealDocument.id)).where(
            DealDocument.project_id == project_id
        )
        count = (await self.db.execute(count_q)).scalar() or 0
        return f"DOC-{count + 1:04d}"

    async def _count_pending_reviews(self, document_id: str) -> int:
        """Count reviews still pending for a document."""
        result = await self.db.execute(
            select(func.count(DocumentReview.id)).where(
                DocumentReview.document_id == document_id,
                DocumentReview.status.in_(["pending", "in_progress"]),
            )
        )
        return result.scalar() or 0

    async def _to_read_schema(self, document: DealDocument) -> DealDocumentRead:
        """Convert model to read schema with computed fields."""
        # Load document type
        doc_type = await self.db.get(DealDocumentType, document.document_type_id)

        # Count versions
        version_count_q = select(func.count(DealDocumentVersion.id)).where(
            DealDocumentVersion.document_id == document.id
        )
        version_count = (await self.db.execute(version_count_q)).scalar() or 0

        # Get latest version number
        max_version_q = select(func.max(DealDocumentVersion.version_number)).where(
            DealDocumentVersion.document_id == document.id
        )
        current_version = (await self.db.execute(max_version_q)).scalar() or 0

        return DealDocumentRead(
            id=UUID(document.id),
            project_id=UUID(document.project_id),
            title=document.title,
            document_number=document.document_number,
            document_type=self._type_to_schema(doc_type) if doc_type else None,
            status=DocumentStatus(document.status),
            content_json=document.content_json,
            content_html=document.content_html,
            template_id=UUID(document.template_id) if document.template_id else None,
            template_version=document.template_version,
            signature_request_id=document.signature_request_id,
            signature_status=document.signature_status,
            filed_to=document.filed_to,
            filed_at=document.filed_at,
            filing_reference=document.filing_reference,
            retention_policy=RetentionPolicy(document.retention_policy),
            legal_hold=document.legal_hold,
            retention_expires_at=document.retention_expires_at,
            artifact_id=UUID(document.artifact_id) if document.artifact_id else None,
            created_by=UserSummary(id=UUID(document.created_by_id)),
            assigned_to=(
                UserSummary(id=UUID(document.assigned_to_id))
                if document.assigned_to_id
                else None
            ),
            version_count=version_count,
            current_version=current_version,
            created_at=document.created_at,
            updated_at=document.updated_at,
        )

    @staticmethod
    def _type_to_schema(dt: DealDocumentType) -> DealDocumentTypeRead:
        """Convert document type model to read schema."""
        return DealDocumentTypeRead(
            id=UUID(dt.id),
            code=dt.code,
            display_name=dt.display_name,
            category=DocumentCategory(dt.category),
            deal_vertical=dt.deal_vertical,
            description=dt.description,
            default_workflow=dt.default_workflow,
            retention_policy=RetentionPolicy(dt.retention_policy),
            requires_signature=dt.requires_signature,
            is_active=dt.is_active,
            sort_order=dt.sort_order,
            created_at=dt.created_at,
            updated_at=dt.updated_at,
        )

    @staticmethod
    def _render_template(template_body: str, variables: dict) -> dict | None:
        """Render a Jinja2 template with variables, returning TipTap JSON."""
        try:
            from jinja2 import BaseLoader, Environment, select_autoescape

            env = Environment(
                loader=BaseLoader(), autoescape=select_autoescape()
            )
            tmpl = env.from_string(template_body)
            rendered = tmpl.render(**variables)
            return json.loads(rendered)
        except Exception:
            return None

    @staticmethod
    def _extract_plaintext(content_json: dict | None) -> str | None:
        """
        Extract plain text from TipTap JSON for full-text search.

        Recursively walks the ProseMirror node tree collecting text nodes.
        """
        if not content_json:
            return None

        texts: list[str] = []

        def _walk(node: dict) -> None:
            if node.get("type") == "text":
                text = node.get("text", "")
                if text:
                    texts.append(text)
            for child in node.get("content", []):
                if isinstance(child, dict):
                    _walk(child)

        _walk(content_json)
        return " ".join(texts) if texts else None
