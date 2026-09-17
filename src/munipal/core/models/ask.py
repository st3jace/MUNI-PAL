"""Durable, owner-scoped Ask history."""

from sqlalchemy import JSON, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from munipal.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin, UUIDType


class AskConversation(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "ask_conversations"

    owner_id: Mapped[str] = mapped_column(UUIDType, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    project_id: Mapped[str] = mapped_column(UUIDType, ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    artifact_id: Mapped[str | None] = mapped_column(UUIDType, ForeignKey("artifacts.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String(120), default="New chat")
    next_sequence: Mapped[int] = mapped_column(Integer, default=1, server_default="1")


class AskMessage(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "ask_messages"
    __table_args__ = (
        UniqueConstraint("conversation_id", "sequence", name="uq_ask_message_sequence"),
    )

    conversation_id: Mapped[str] = mapped_column(
        UUIDType,
        ForeignKey("ask_conversations.id", ondelete="CASCADE"),
        index=True,
    )
    sequence: Mapped[int] = mapped_column(Integer)
    role: Mapped[str] = mapped_column(String(20))
    kind: Mapped[str] = mapped_column(String(20))
    content: Mapped[str] = mapped_column(Text)
    citations: Mapped[list] = mapped_column(JSON, default=list)
