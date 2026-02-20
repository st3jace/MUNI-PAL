"""
Security audit event emission.
"""

import logging
from datetime import UTC, datetime
from typing import Any

audit_logger = logging.getLogger("munipal.audit")


class AuditService:
    """Emit structured security-relevant audit events."""

    @staticmethod
    def emit_event(
        *,
        actor_id: str,
        action: str,
        target_type: str,
        target_id: str,
        project_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        event = {
            "timestamp": datetime.now(UTC).isoformat(),
            "actor_id": actor_id,
            "action": action,
            "target_type": target_type,
            "target_id": target_id,
            "project_id": project_id,
            "metadata": metadata or {},
        }
        audit_logger.info("security_audit_event", extra={"audit_event": event})
        return event
