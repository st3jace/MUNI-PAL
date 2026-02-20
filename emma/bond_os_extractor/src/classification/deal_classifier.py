from __future__ import annotations

import logging
from decimal import Decimal

from ..schema.deal_record import DealRecord

logger = logging.getLogger("bond_os_extractor.classification")


# ---------------------------------------------------------------------------
# Classification taxonomies
# ---------------------------------------------------------------------------

PRIMARY_TYPES = {
    "general_obligation": "GO_UNLIMITED",
    "revenue": None,  # needs further classification
    "conduit_revenue": None,
    "special_assessment": "SPECIAL_ASSESSMENT",
    "tax_increment": "TAX_INCREMENT",
    "moral_obligation": "MORAL_OBLIGATION",
    "double_barrel": "DOUBLE_BARREL",
    "lease_revenue": "LEASE_REVENUE",
    "certificates_of_participation": "COPs",
    "industrial_development": "CONDUIT_INDUSTRIAL",
    "private_activity": "PRIVATE_ACTIVITY",
    "qualified_501c3": "CONDUIT_501C3",
}

REVENUE_SUBTYPES = {
    "water": "REVENUE_WATER_SEWER",
    "sewer": "REVENUE_WATER_SEWER",
    "electric": "REVENUE_ELECTRIC",
    "hospital": "REVENUE_HEALTHCARE",
    "health": "REVENUE_HEALTHCARE",
    "university": "REVENUE_HIGHER_ED",
    "college": "REVENUE_HIGHER_ED",
    "housing": "REVENUE_HOUSING",
    "transport": "REVENUE_TRANSPORTATION",
    "highway": "REVENUE_TRANSPORTATION",
    "toll": "REVENUE_TRANSPORTATION",
    "airport": "REVENUE_AIRPORT",
    "port": "REVENUE_PORT",
    "solid waste": "REVENUE_SOLID_WASTE",
    "waste": "REVENUE_SOLID_WASTE",
    "landfill": "REVENUE_SOLID_WASTE",
    "industrial": "REVENUE_INDUSTRIAL_DEVELOPMENT",
}

# Moody's / S&P / Fitch rating tiers
IG_HIGH = {"Aaa", "Aa1", "Aa2", "Aa3", "AAA", "AA+", "AA", "AA-"}
IG_MID = {"A1", "A2", "A3", "A+", "A", "A-"}
IG_LOW = {"Baa1", "Baa2", "Baa3", "BBB+", "BBB", "BBB-"}
BELOW_IG = {"Ba1", "Ba2", "Ba3", "B1", "B2", "B3", "BB+", "BB", "BB-", "B+", "B", "B-",
            "Caa1", "Caa2", "Caa3", "CCC+", "CCC", "CCC-", "CC", "C", "D"}


def classify_primary(record: DealRecord) -> str:
    """Classify by security type."""
    bond_type = record.structure.bond_type
    if not bond_type:
        return "UNCLASSIFIED"

    # Direct map
    mapped = PRIMARY_TYPES.get(bond_type)
    if mapped:
        return mapped

    # Revenue bonds need subtype from title/description
    title = (record.identity.official_title or "").lower()
    issuer = (record.identity.issuer_name or "").lower()
    combined = f"{title} {issuer}"

    for keyword, subtype in REVENUE_SUBTYPES.items():
        if keyword in combined:
            return subtype

    return "REVENUE_OTHER"


def classify_secondary(record: DealRecord) -> str:
    """Classify by structural features."""
    parts: list[str] = []

    # Interest type
    it = record.structure.interest_type
    if it == "fixed_rate":
        parts.append("FIXED_RATE")
    elif it == "variable_rate":
        parts.append("VARIABLE_RATE")
    elif it in ("capital_appreciation", "convertible_cab"):
        parts.append("CAB")
    elif it == "zero_coupon":
        parts.append("ZERO_COUPON")

    # CAB
    if record.structure.cab_enabled and "CAB" not in parts:
        parts.append("CAB")

    # SLB / ESG
    if record.structure.slb_enabled:
        parts.append("SUSTAINABILITY_LINKED")
    elif record.structure.green_bond:
        parts.append("GREEN_BOND")
    elif record.structure.social_bond:
        parts.append("SOCIAL_BOND")

    # Refunding
    if record.refunding and record.refunding.is_refunding:
        rt = record.refunding.refunding_type
        if rt == "advance_refunding":
            parts.append("REFUNDING_ADVANCE")
        elif rt == "current_refunding":
            parts.append("REFUNDING_CURRENT")
        else:
            parts.append("REFUNDING")
    else:
        parts.append("NEW_MONEY")

    return "+".join(parts) if parts else "UNCLASSIFIED"


def classify_credit(record: DealRecord) -> str:
    """Classify by credit quality."""
    if not record.ratings or not record.ratings.ratings:
        return "NON_RATED"

    for r in record.ratings.ratings:
        rating = r.rating
        if rating in IG_HIGH:
            return "INVESTMENT_GRADE_HIGH"
        if rating in IG_MID:
            return "INVESTMENT_GRADE_MID"
        if rating in IG_LOW:
            return "INVESTMENT_GRADE_LOW"
        if rating in BELOW_IG:
            return "BELOW_INVESTMENT_GRADE"

    return "NON_RATED"


def classify_size(record: DealRecord) -> str:
    """Classify by par amount."""
    par = record.structure.par_amount
    if par is None:
        return "UNKNOWN"
    if par < 10_000_000:
        return "MICRO"
    if par < 50_000_000:
        return "SMALL"
    if par < 250_000_000:
        return "MEDIUM"
    if par < 1_000_000_000:
        return "LARGE"
    return "JUMBO"


def classify_deal(record: DealRecord) -> DealRecord:
    """Run all classifiers and populate the DealRecord classification fields."""
    record.primary_classification = classify_primary(record)
    record.secondary_classification = classify_secondary(record)
    record.tertiary_classification = classify_credit(record)
    record.size_classification = classify_size(record)
    logger.info(
        "Classified: %s | %s | %s | %s",
        record.primary_classification,
        record.secondary_classification,
        record.tertiary_classification,
        record.size_classification,
    )
    return record
