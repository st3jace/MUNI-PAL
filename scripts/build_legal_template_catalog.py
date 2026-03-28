"""
Build a legal-template catalog from archived EMMA crawler PDFs.

The output is a machine-readable corpus index that can drive
deal-structure-based clause/template recommendations.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pypdf import PdfReader

DOC_CLASS_PATTERNS: list[tuple[str, tuple[re.Pattern[str], ...]]] = [
    ("master_trust_indenture", (re.compile(r"master[_\s-]*trust[_\s-]*indenture"),)),
    ("trust_indenture", (re.compile(r"trust[_\s-]*indenture"), re.compile(r"bond[_\s-]*indenture"))),
    (
        "letter_of_credit_reimbursement_agreement",
        (re.compile(r"letter[_\s-]*of[_\s-]*credit"), re.compile(r"reimbursement[_\s-]*agreement")),
    ),
    ("loan_agreement", (re.compile(r"loan[_\s-]*agreement"),)),
    ("bond_purchase_agreement", (re.compile(r"bond[_\s-]*purchase[_\s-]*agreement"),)),
    ("remarketing_agreement", (re.compile(r"remarketing[_\s-]*agreement"),)),
    ("isda_master_agreement", (re.compile(r"isda"), re.compile(r"master[_\s-]*agreement"))),
    ("continuing_disclosure_agreement", (re.compile(r"continuing[_\s-]*disclosure"),)),
    ("official_statement", (re.compile(r"official[_\s-]*statement"), re.compile(r"\bos\b"))),
    ("board_resolution", (re.compile(r"board[_\s-]*resolution"), re.compile(r"authorizing[_\s-]*ordinance"))),
    ("tax_certificate", (re.compile(r"tax[_\s-]*certificate"), re.compile(r"8038"))),
    ("tax_opinion", (re.compile(r"tax[_\s-]*opinion"), re.compile(r"bond[_\s-]*counsel[_\s-]*opinion"))),
    ("nda", (re.compile(r"\bnda\b"), re.compile(r"non[_\s-]*disclosure"))),
    ("letter_of_intent", (re.compile(r"letter[_\s-]*of[_\s-]*intent"), re.compile(r"\bloi\b"))),
    ("limited_partnership_agreement", (re.compile(r"limited[_\s-]*partnership[_\s-]*agreement"), re.compile(r"\blpa\b"))),
    ("private_placement_memorandum", (re.compile(r"private[_\s-]*placement[_\s-]*memorandum"), re.compile(r"\bppm\b"))),
    ("side_letter", (re.compile(r"side[_\s-]*letter"),)),
    ("subscription_agreement", (re.compile(r"subscription[_\s-]*agreement"), re.compile(r"sub[_\s-]*agmt"))),
    ("credit_agreement", (re.compile(r"credit[_\s-]*agreement"),)),
    ("purchase_and_sale_agreement", (re.compile(r"purchase[_\s-]*and[_\s-]*sale"), re.compile(r"\bspa\b"))),
    ("operating_agreement", (re.compile(r"operating[_\s-]*agreement"),)),
    ("tip_fee_agreement", (re.compile(r"tip[_\s-]*fee"),)),
    ("power_purchase_agreement", (re.compile(r"power[_\s-]*purchase[_\s-]*agreement"), re.compile(r"\bppa\b"))),
    ("interconnection_agreement", (re.compile(r"interconnection[_\s-]*agreement"),)),
    ("environmental_permit", (re.compile(r"environmental[_\s-]*permit"), re.compile(r"phase[_\s-]*i"))),
    ("lease_agreement", (re.compile(r"lease[_\s-]*agreement"), re.compile(r"\blease\b"))),
    ("property_management_agreement", (re.compile(r"property[_\s-]*management[_\s-]*agreement"),)),
    ("event_notice", (re.compile(r"event[_\s-]*disclosure"), re.compile(r"material[_\s-]*event"), re.compile(r"financial[_\s-]*obligation"))),
    ("financial_disclosure", (re.compile(r"financial[_\s-]*disclosure"), re.compile(r"annual[_\s-]*financial"))),
    ("audited_financials", (re.compile(r"audited[_\s-]*financial"), re.compile(r"quarterly[_\s-]*report"))),
]


FEATURE_PATTERNS: dict[str, tuple[re.Pattern[str], ...]] = {
    "additional_bonds_test": (re.compile(r"additional bonds", re.IGNORECASE), re.compile(r"parity debt", re.IGNORECASE)),
    "debt_service_reserve_fund": (re.compile(r"debt service reserve", re.IGNORECASE), re.compile(r"reserve fund", re.IGNORECASE)),
    "rate_covenant": (re.compile(r"rate covenant", re.IGNORECASE), re.compile(r"coverage ratio", re.IGNORECASE)),
    "flow_of_funds": (re.compile(r"flow of funds", re.IGNORECASE), re.compile(r"funds and accounts", re.IGNORECASE)),
    "event_of_default": (re.compile(r"event of default", re.IGNORECASE), re.compile(r"default", re.IGNORECASE)),
    "cross_default": (re.compile(r"cross default", re.IGNORECASE),),
    "tip_fee_escalator": (re.compile(r"tip fee", re.IGNORECASE), re.compile(r"escalat", re.IGNORECASE)),
    "power_purchase_take_or_pay": (re.compile(r"power purchase", re.IGNORECASE), re.compile(r"take[- ]or[- ]pay", re.IGNORECASE)),
    "force_majeure": (re.compile(r"force majeure", re.IGNORECASE),),
    "covenant_monitoring": (re.compile(r"covenant", re.IGNORECASE), re.compile(r"dscr", re.IGNORECASE)),
    "distribution_waterfall": (re.compile(r"waterfall", re.IGNORECASE), re.compile(r"carried interest", re.IGNORECASE)),
    "clawback": (re.compile(r"clawback", re.IGNORECASE),),
    "indemnification": (re.compile(r"indemnif", re.IGNORECASE),),
    "representations_warranties": (re.compile(r"representations? and warranties?", re.IGNORECASE),),
    "continuing_disclosure": (re.compile(r"continuing disclosure", re.IGNORECASE), re.compile(r"15c2-12", re.IGNORECASE)),
}


LEGAL_TEMPLATE_CLASSES = {
    "master_trust_indenture",
    "trust_indenture",
    "letter_of_credit_reimbursement_agreement",
    "loan_agreement",
    "bond_purchase_agreement",
    "remarketing_agreement",
    "isda_master_agreement",
    "continuing_disclosure_agreement",
    "board_resolution",
    "tax_certificate",
    "tax_opinion",
    "nda",
    "letter_of_intent",
    "limited_partnership_agreement",
    "private_placement_memorandum",
    "side_letter",
    "subscription_agreement",
    "credit_agreement",
    "purchase_and_sale_agreement",
    "operating_agreement",
    "tip_fee_agreement",
    "power_purchase_agreement",
    "interconnection_agreement",
    "environmental_permit",
    "lease_agreement",
    "property_management_agreement",
}


DOC_CLASS_TO_DMS_CODE: dict[str, list[str]] = {
    "master_trust_indenture": ["trust_indenture"],
    "trust_indenture": ["trust_indenture"],
    "letter_of_credit_reimbursement_agreement": ["letter_of_credit"],
    "loan_agreement": ["loan_agreement"],
    "bond_purchase_agreement": ["bond_purchase_agreement"],
    "remarketing_agreement": ["remarketing_agreement"],
    "isda_master_agreement": ["isda_master_agreement"],
    "continuing_disclosure_agreement": ["continuing_disclosure_agreement"],
    "official_statement": ["official_statement", "preliminary_official_statement"],
    "board_resolution": ["board_resolution"],
    "tax_certificate": ["tax_certificate"],
    "tax_opinion": ["tax_opinion"],
    "nda": ["nda"],
    "letter_of_intent": ["loi_term_sheet"],
}


SUGGESTED_NEW_DMS_CODES: dict[str, str] = {
    "limited_partnership_agreement": "limited_partnership_agreement",
    "private_placement_memorandum": "private_placement_memorandum",
    "side_letter": "side_letter",
    "subscription_agreement": "subscription_agreement",
    "credit_agreement": "credit_agreement",
    "purchase_and_sale_agreement": "purchase_and_sale_agreement",
    "operating_agreement": "operating_agreement",
    "tip_fee_agreement": "tip_fee_agreement",
    "power_purchase_agreement": "power_purchase_agreement",
    "interconnection_agreement": "interconnection_agreement",
    "environmental_permit": "environmental_permit",
    "lease_agreement": "lease_agreement",
    "property_management_agreement": "property_management_agreement",
}


@dataclass
class BuildResult:
    json_path: Path
    markdown_path: Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _default_pdf_root() -> Path:
    return _repo_root() / "emma" / "emma_crawler" / "output"


def _default_output_dir() -> Path:
    return _repo_root() / "reports" / "legal_corpus"


def _timestamp() -> str:
    return datetime.now(UTC).strftime("%Y%m%d_%H%M%S")


def _normalize_name(path: Path) -> str:
    return path.stem.lower().replace("-", "_").replace(" ", "_")


def _classify(path: Path) -> str:
    name = _normalize_name(path)
    for class_name, patterns in DOC_CLASS_PATTERNS:
        if all(pattern.search(name) for pattern in patterns):
            return class_name
    return "other"


def _extract_sector(path: Path, pdf_root: Path) -> str:
    try:
        rel = path.relative_to(pdf_root)
        return rel.parts[0]
    except Exception:  # noqa: BLE001
        return "unknown"


def _extract_text(path: Path, pages: int) -> str:
    try:
        reader = PdfReader(str(path))
        chunks = []
        for page in reader.pages[:pages]:
            text = page.extract_text() or ""
            if text:
                chunks.append(text)
        return "\n".join(chunks)
    except Exception:  # noqa: BLE001
        return ""


def _scan_existing_muni_doc_codes(repo_root: Path) -> set[str]:
    migration = (
        repo_root
        / "alembic"
        / "versions"
        / "20260226_0001_g7h8i9j0k1l2_add_document_management_system.py"
    )
    if not migration.exists():
        return set()

    content = migration.read_text(encoding="utf-8", errors="ignore")
    return set(re.findall(r"'code':\s*'([^']+)'", content))


def _write_markdown(payload: dict[str, Any], path: Path) -> None:
    summary = payload["summary"]
    lines = [
        "# Legal Template Catalog",
        "",
        f"- Generated (UTC): `{payload['generated_at_utc']}`",
        f"- PDF root: `{payload['pdf_root']}`",
        f"- PDFs scanned: `{summary['total_pdfs_scanned']}`",
        f"- Legal-template candidates: `{summary['legal_template_candidates']}`",
        f"- PDF text parse errors: `{summary['pdf_text_parse_errors']}`",
        "",
        "## Sector Distribution",
        "",
        "| Sector | PDF Count |",
        "|---|---:|",
    ]
    for sector, count in summary["by_sector"].items():
        lines.append(f"| {sector} | {count} |")

    lines.extend(
        [
            "",
            "## Top Document Classes",
            "",
            "| Class | Count | Mapped DMS Codes | Top Features |",
            "|---|---:|---|---|",
        ]
    )
    for item in payload["document_classes"][:20]:
        top_features = ", ".join(f["feature"] for f in item["top_features"][:4]) or "-"
        mapped = ", ".join(item["mapped_document_type_codes"]) or "-"
        lines.append(
            f"| {item['class_name']} | {item['count']} | {mapped} | {top_features} |"
        )

    lines.extend(["", "## Unmapped High-Volume Classes", ""])
    if payload["unmapped_high_volume_classes"]:
        lines.extend(["| Class | Count | Suggested DMS Code |", "|---|---:|---|"])
        for item in payload["unmapped_high_volume_classes"]:
            lines.append(
                f"| {item['class_name']} | {item['count']} | {item['suggested_document_type_code']} |"
            )
    else:
        lines.append("No high-volume unmapped classes found.")

    lines.extend(["", "## Recommendations", ""])
    for recommendation in payload["recommendations"]:
        lines.append(f"- {recommendation}")

    path.write_text("\n".join(lines), encoding="utf-8")


def build_catalog(
    *,
    pdf_root: Path,
    output_dir: Path,
    max_pdfs: int,
    text_pages: int,
    text_samples_per_class: int,
    min_unmapped_count: int,
) -> BuildResult:
    output_dir.mkdir(parents=True, exist_ok=True)

    all_pdfs = sorted(pdf_root.rglob("*.pdf"))
    if max_pdfs > 0:
        all_pdfs = all_pdfs[:max_pdfs]

    existing_doc_codes = _scan_existing_muni_doc_codes(_repo_root())

    by_sector = Counter()
    class_counts = Counter()
    class_samples: dict[str, list[str]] = defaultdict(list)
    class_feature_counts: dict[str, Counter[str]] = defaultdict(Counter)
    global_feature_counts = Counter()
    parse_errors = 0

    text_sample_count_by_class = Counter()

    for path in all_pdfs:
        doc_class = _classify(path)
        class_counts[doc_class] += 1
        by_sector[_extract_sector(path, pdf_root)] += 1

        try:
            rel = str(path.relative_to(_repo_root()))
        except ValueError:
            rel = str(path)
        if len(class_samples[doc_class]) < 8:
            class_samples[doc_class].append(rel)

        searchable_blob = _normalize_name(path)
        if (
            doc_class in LEGAL_TEMPLATE_CLASSES
            and text_samples_per_class > 0
            and text_sample_count_by_class[doc_class] < text_samples_per_class
        ):
            text_sample_count_by_class[doc_class] += 1
            extracted = _extract_text(path, text_pages)
            if extracted:
                searchable_blob += "\n" + extracted.lower()
            else:
                parse_errors += 1

        for feature_name, patterns in FEATURE_PATTERNS.items():
            if any(pattern.search(searchable_blob) for pattern in patterns):
                class_feature_counts[doc_class][feature_name] += 1
                global_feature_counts[feature_name] += 1

    document_classes: list[dict[str, Any]] = []
    for class_name, count in class_counts.most_common():
        mapped_codes = DOC_CLASS_TO_DMS_CODE.get(class_name, [])
        top_features = [
            {"feature": feature, "count": feature_count}
            for feature, feature_count in class_feature_counts[class_name].most_common(8)
        ]
        document_classes.append(
            {
                "class_name": class_name,
                "count": count,
                "template_candidate": class_name in LEGAL_TEMPLATE_CLASSES,
                "mapped_document_type_codes": mapped_codes,
                "mapped_codes_present_in_phase1_seed": [
                    code for code in mapped_codes if code in existing_doc_codes
                ],
                "top_features": top_features,
                "sample_files": class_samples[class_name],
            }
        )

    unmapped_high_volume_classes = []
    for class_name, count in class_counts.items():
        if count < min_unmapped_count:
            continue
        if class_name == "other":
            continue
        if DOC_CLASS_TO_DMS_CODE.get(class_name):
            continue
        suggested = SUGGESTED_NEW_DMS_CODES.get(class_name, class_name)
        unmapped_high_volume_classes.append(
            {
                "class_name": class_name,
                "count": count,
                "suggested_document_type_code": suggested,
            }
        )
    unmapped_high_volume_classes.sort(key=lambda item: item["count"], reverse=True)

    payload: dict[str, Any] = {
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "pdf_root": str(pdf_root),
        "summary": {
            "total_pdfs_scanned": len(all_pdfs),
            "legal_template_candidates": int(
                sum(class_counts[name] for name in LEGAL_TEMPLATE_CLASSES if name in class_counts)
            ),
            "pdf_text_parse_errors": parse_errors,
            "by_sector": dict(sorted(by_sector.items())),
        },
        "top_features": [
            {"feature": feature, "count": count}
            for feature, count in global_feature_counts.most_common(20)
        ],
        "document_classes": document_classes,
        "unmapped_high_volume_classes": unmapped_high_volume_classes,
        "phase1_seeded_document_type_codes": sorted(existing_doc_codes),
        "recommendations": [
            "Use this catalog as an advisory layer for template and clause recommendation workflows.",
            "Prioritize template authoring for high-volume unmapped classes first.",
            "Keep human-in-the-loop approval on clause substitution and template execution.",
            "Wire covenant-related features to monitoring calculations to enforce model-to-document consistency.",
        ],
    }

    stamp = _timestamp()
    json_path = output_dir / f"legal_template_catalog_{stamp}.json"
    markdown_path = output_dir / f"legal_template_catalog_{stamp}.md"
    json_latest = output_dir / "legal_template_catalog_latest.json"
    markdown_latest = output_dir / "legal_template_catalog_latest.md"

    json_text = json.dumps(payload, indent=2)
    json_path.write_text(json_text, encoding="utf-8")
    json_latest.write_text(json_text, encoding="utf-8")
    _write_markdown(payload, markdown_path)
    _write_markdown(payload, markdown_latest)

    return BuildResult(json_path=json_path, markdown_path=markdown_path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build legal template catalog from EMMA PDFs.")
    parser.add_argument("--pdf-root", type=Path, default=_default_pdf_root())
    parser.add_argument("--output-dir", type=Path, default=_default_output_dir())
    parser.add_argument(
        "--max-pdfs",
        type=int,
        default=0,
        help="Optional scan cap for faster iteration (0 = all PDFs).",
    )
    parser.add_argument(
        "--text-pages",
        type=int,
        default=1,
        help="Number of pages to parse per sampled PDF.",
    )
    parser.add_argument(
        "--text-samples-per-class",
        type=int,
        default=20,
        help="PDF text samples to parse per document class.",
    )
    parser.add_argument(
        "--min-unmapped-count",
        type=int,
        default=25,
        help="Minimum class frequency to include in unmapped recommendations.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = build_catalog(
        pdf_root=args.pdf_root,
        output_dir=args.output_dir,
        max_pdfs=args.max_pdfs,
        text_pages=args.text_pages,
        text_samples_per_class=args.text_samples_per_class,
        min_unmapped_count=args.min_unmapped_count,
    )
    print(f"Wrote catalog JSON: {result.json_path}")
    print(f"Wrote catalog markdown: {result.markdown_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
