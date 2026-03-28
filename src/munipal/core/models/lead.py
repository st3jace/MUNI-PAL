"""
Sensing Lead & Funnel Tracking models.

Captures prospect information when they request a combined PDF report,
and tracks their progression through the sensing tool funnel.
"""

from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from munipal.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class SensingLead(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """A prospect captured through the sensing tool funnel."""

    __tablename__ = "sensing_leads"

    # Contact info (required for PDF download)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    organization: Mapped[str] = mapped_column(String(255), nullable=False)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Deal context
    sector: Mapped[str] = mapped_column(String(50), nullable=False)
    deal_size_estimate: Mapped[float | None] = mapped_column(Float, nullable=True)
    state: Mapped[str | None] = mapped_column(String(5), nullable=True)
    expected_rating: Mapped[str | None] = mapped_column(String(10), nullable=True)

    # Referral
    referral_source: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Funnel stage tracking
    funnel_stage: Mapped[str] = mapped_column(
        String(50), nullable=False, default="report_requested"
    )
    # Possible stages: report_requested, report_downloaded,
    #                  contacted, qualified, engaged

    # Report data snapshot (JSON blobs stored as text)
    market_intel_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    benchmark_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    readiness_json: Mapped[str | None] = mapped_column(Text, nullable=True)


class SensingEvent(Base, UUIDPrimaryKeyMixin):
    """Tracks individual interactions with sensing tools for funnel analytics."""

    __tablename__ = "sensing_events"

    # Link to lead (nullable — events can happen before lead capture)
    lead_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)

    # Session tracking (anonymous until lead capture)
    session_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    # Event details
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    # Event types: page_view, market_intel_loaded, benchmark_run,
    #              readiness_scored, report_requested, report_downloaded

    sector: Mapped[str | None] = mapped_column(String(50), nullable=True)
    event_data: Mapped[str | None] = mapped_column(Text, nullable=True)

    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
