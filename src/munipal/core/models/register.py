"""Private per-deal intake, purchases, source files and immutable report snapshots."""

from sqlalchemy import JSON, ForeignKey, Integer, LargeBinary, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from munipal.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin, UUIDType


class RegisterDeal(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "register_deals"

    owner_id: Mapped[str] = mapped_column(UUIDType, ForeignKey("users.id"), index=True)
    tenant_id: Mapped[str] = mapped_column(String(255))
    name: Mapped[str] = mapped_column(String(200))
    legal_name: Mapped[str] = mapped_column(String(255))
    professional_contact: Mapped[str] = mapped_column(String(1000))
    consent_version: Mapped[str] = mapped_column(String(50), default="register-portal-v1")
    payment_status: Mapped[str] = mapped_column(String(30), default="awaiting_quote")
    amount_cents: Mapped[int | None] = mapped_column(Integer)
    currency: Mapped[str] = mapped_column(String(3), default="usd")
    quote_note: Mapped[str | None] = mapped_column(Text)
    quote_version: Mapped[int] = mapped_column(Integer, default=0)
    quoted_by: Mapped[str | None] = mapped_column(UUIDType, ForeignKey("users.id"))
    checkout_session_id: Mapped[str | None] = mapped_column(String(255), unique=True)
    checkout_url: Mapped[str | None] = mapped_column(Text)
    payment_intent_id: Mapped[str | None] = mapped_column(String(255), unique=True)
    report_sequence: Mapped[int] = mapped_column(Integer, default=0)


class RegisterDocument(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "register_documents"
    deal_id: Mapped[str] = mapped_column(
        UUIDType, ForeignKey("register_deals.id", ondelete="CASCADE"), index=True
    )
    filename: Mapped[str] = mapped_column(String(200))
    sha256: Mapped[str] = mapped_column(String(64))
    size: Mapped[int] = mapped_column(Integer)
    content: Mapped[bytes] = mapped_column(LargeBinary, deferred=True)
    extracted: Mapped[list] = mapped_column(JSON, deferred=True)
    __table_args__ = (UniqueConstraint("deal_id", "sha256", name="uq_register_document_hash"),)


class RegisterFolder(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "register_folders"
    deal_id: Mapped[str] = mapped_column(
        UUIDType, ForeignKey("register_deals.id", ondelete="CASCADE"), index=True
    )
    url: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(30), default="awaiting_import")
    note: Mapped[str | None] = mapped_column(Text)
    updated_by: Mapped[str | None] = mapped_column(UUIDType, ForeignKey("users.id"))


class RegisterReport(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "register_reports"
    deal_id: Mapped[str] = mapped_column(
        UUIDType, ForeignKey("register_deals.id", ondelete="CASCADE"), index=True
    )
    version: Mapped[int] = mapped_column(Integer)
    kind: Mapped[str] = mapped_column(String(30), default="candidate_package")
    note: Mapped[str | None] = mapped_column(Text)
    published_by: Mapped[str | None] = mapped_column(UUIDType, ForeignKey("users.id"))
    candidate_count: Mapped[int] = mapped_column(Integer)
    document_count: Mapped[int] = mapped_column(Integer)
    content: Mapped[bytes] = mapped_column(LargeBinary, deferred=True)
    sha256: Mapped[str] = mapped_column(String(64))
    __table_args__ = (UniqueConstraint("deal_id", "version", name="uq_register_report_version"),)


class RegisterPaymentReversal(Base, TimestampMixin):
    """A refund can arrive before checkout completion; preserve its revocation."""

    __tablename__ = "register_payment_reversals"
    payment_intent_id: Mapped[str] = mapped_column(String(255), primary_key=True)
