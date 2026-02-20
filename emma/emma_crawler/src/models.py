from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class QueueSecurity:
    detail_url: str
    description: str = ""
    state: str = ""
    principal_amount: int | None = None
    coupon: str = ""
    maturity_date: str = ""
    dated_date: str = ""
    source_page: int | None = None
    url_hash: str = ""

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        if not payload.get("url_hash"):
            payload["url_hash"] = self.detail_url.rstrip("/").split("/")[-1]
        return payload


@dataclass
class SecurityRecord:
    cusip: str
    emma_url: str
    crawl_timestamp: str = field(default_factory=utc_now_iso)
    extraction_status: dict[str, str] = field(default_factory=dict)
    snapshot: dict[str, Any] = field(default_factory=dict)
    interest_rates: list[dict[str, Any]] = field(default_factory=list)
    trades: list[dict[str, Any]] = field(default_factory=list)
    ratings: list[dict[str, Any]] = field(default_factory=list)
    disclosures: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "cusip": self.cusip,
            "crawl_metadata": {
                "crawl_timestamp": self.crawl_timestamp,
                "emma_url": self.emma_url,
                "extraction_status": self.extraction_status,
            },
            "snapshot": self.snapshot,
            "interest_rates": self.interest_rates,
            "trades": self.trades,
            "ratings": self.ratings,
            "disclosures": self.disclosures,
        }
