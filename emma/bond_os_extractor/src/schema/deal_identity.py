from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel


class DealIdentity(BaseModel):
    # Document identification
    cusip_base: str | None = None
    cusip_series: list[str] = []
    document_type: Literal["OS", "POS", "supplement", "remarketing"] | None = None
    dated_date: date | None = None
    sale_date: date | None = None
    delivery_date: date | None = None

    # Parties — issuer
    issuer_name: str | None = None
    issuer_type: Literal[
        "state", "county", "city", "town", "village",
        "special_district", "authority", "ida",
        "school_district", "utility", "housing", "health",
    ] | None = None
    issuer_state: str | None = None
    issuer_county: str | None = None

    # Parties — borrower (conduit deals)
    borrower_name: str | None = None
    borrower_type: str | None = None

    # Parties — professionals
    trustee_name: str | None = None
    bond_counsel: str | None = None
    underwriter_names: list[str] = []
    underwriter_counsel: str | None = None
    municipal_advisor: str | None = None
    disclosure_counsel: str | None = None
    paying_agent: str | None = None
    registrar: str | None = None
    verification_agent: str | None = None

    # Series
    series_name: str | None = None
    official_title: str | None = None
