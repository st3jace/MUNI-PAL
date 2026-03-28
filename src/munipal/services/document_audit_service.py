"""
Document audit service - immutable audit trail for all document operations.

Every document action (create, edit, sign, view, etc.) is logged here
for compliance with MSRB G-9, SEC 15c2-12, and IRS retention requirements.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from munipal.core.models.deal_document import DocumentAuditLog
from munipal.core.schemas.deal_document import AuditEntryRead


class DocumentAuditService:
    """Immutable, append-only audit log for document operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def log(
        self,
        document_id: UUID,
        actor_id: str,
        action: str,
        details: dict | None = None,
        actor_email: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> None:
        """Append an audit entry. Never fails silently."""
        entry = DocumentAuditLog(
            document_id=str(document_id),
            actor_id=actor_id,
            actor_email=actor_email,
            action=action,
            details=details or {},
            ip_address=ip_address,
            user_agent=user_agent,
        )
        self.db.add(entry)
        await self.db.flush()

    async def get_log(
        self,
        document_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[AuditEntryRead], int]:
        """Get paginated audit log for a document."""
        base = select(DocumentAuditLog).where(
            DocumentAuditLog.document_id == str(document_id)
        )
        count_q = select(func.count(DocumentAuditLog.id)).where(
            DocumentAuditLog.document_id == str(document_id)
        )

        total = (await self.db.execute(count_q)).scalar() or 0

        query = base.order_by(DocumentAuditLog.timestamp.desc()).offset(skip).limit(limit)
        result = await self.db.execute(query)
        entries = result.scalars().all()

        return [
            AuditEntryRead(
                id=UUID(e.id),
                document_id=UUID(e.document_id),
                actor_id=UUID(e.actor_id),
                actor_email=e.actor_email,
                action=e.action,
                details=e.details,
                ip_address=e.ip_address,
                timestamp=e.timestamp,
            )
            for e in entries
        ], total

    async def get_project_audit(
        self,
        project_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[AuditEntryRead], int]:
        """Get audit log for all documents in a project."""
        from munipal.core.models.deal_document import DealDocument

        base = (
            select(DocumentAuditLog)
            .join(DealDocument, DocumentAuditLog.document_id == DealDocument.id)
            .where(DealDocument.project_id == str(project_id))
        )
        count_q = (
            select(func.count(DocumentAuditLog.id))
            .join(DealDocument, DocumentAuditLog.document_id == DealDocument.id)
            .where(DealDocument.project_id == str(project_id))
        )

        total = (await self.db.execute(count_q)).scalar() or 0

        query = base.order_by(DocumentAuditLog.timestamp.desc()).offset(skip).limit(limit)
        result = await self.db.execute(query)
        entries = result.scalars().all()

        return [
            AuditEntryRead(
                id=UUID(e.id),
                document_id=UUID(e.document_id),
                actor_id=UUID(e.actor_id),
                actor_email=e.actor_email,
                action=e.action,
                details=e.details,
                ip_address=e.ip_address,
                timestamp=e.timestamp,
            )
            for e in entries
        ], total
