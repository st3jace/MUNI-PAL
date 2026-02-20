from munipal.services.audit_service import AuditService


def test_emit_event_returns_structured_payload():
    event = AuditService.emit_event(
        actor_id="user-123",
        action="approve_fact",
        target_type="fact",
        target_id="fact-456",
        project_id="project-789",
        metadata={"reason": "reviewed"},
    )

    assert event["actor_id"] == "user-123"
    assert event["action"] == "approve_fact"
    assert event["target_type"] == "fact"
    assert event["target_id"] == "fact-456"
    assert event["project_id"] == "project-789"
    assert event["metadata"] == {"reason": "reviewed"}
    assert event["timestamp"]
