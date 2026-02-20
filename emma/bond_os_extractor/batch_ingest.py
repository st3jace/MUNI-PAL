"""Batch ingest PDFs from EMMA crawler output.

Default mode: Finds all substantial OS/POS PDFs (>100KB), excludes stubs
and supplements, deduplicates by SHA256, and runs the OS extraction pipeline.

With --all-types: Finds ALL PDFs and routes each to the appropriate
extraction module (rating action, event filing, financial report, or OS).
"""
from __future__ import annotations

import hashlib
import sys
import time
from pathlib import Path

# Paths
DEFAULT_EMMA_PDFS = Path(r"C:\Users\st3ja\OneDrive\Documents\MEGA\PROJECTS\INNOVATION FACTORY\MUNI-PAL\emma\emma_crawler\output\pdfs")


def _get_pdf_root() -> Path:
    """Get the PDF root from CLI args or use default."""
    for arg in sys.argv[1:]:
        if not arg.startswith("--"):
            p = Path(arg)
            if p.is_dir():
                return p
    return DEFAULT_EMMA_PDFS

# Patterns to exclude (supplements, stubs, fact sheets)
EXCLUDE_KEYWORDS = [
    "Remarketing",
    "Supplement",
    "Fact_Sheet",
    "Understanding",
    "REOFFERING",
    "_s.pdf",         # EMMA summary stubs (tiny ~10KB link pages)
]

MIN_FILE_SIZE = 100 * 1024  # 100 KB — skip tiny stubs
# Smaller threshold for non-OS docs (rating actions can be small)
MIN_FILE_SIZE_ALL = 10 * 1024  # 10 KB


def quick_hash(path: Path) -> str:
    """Fast SHA256 of first 64KB for dedup without reading entire file."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        h.update(f.read(65536))
    return h.hexdigest()


def find_os_pdfs() -> list[Path]:
    """Find all real Official Statement / Preliminary OS PDFs."""
    all_pdfs: list[Path] = []
    pdf_root = _get_pdf_root()
    for pdf in pdf_root.rglob("*Official_Statement*.pdf"):
        name = pdf.name
        # Check exclusions
        if any(kw in name for kw in EXCLUDE_KEYWORDS):
            continue
        # Must be substantial (>100KB)
        if pdf.stat().st_size < MIN_FILE_SIZE:
            continue
        all_pdfs.append(pdf)

    # Also find Preliminary Official Statements
    for pdf in pdf_root.rglob("*Preliminary_Official_Statement*.pdf"):
        name = pdf.name
        if any(kw in name for kw in EXCLUDE_KEYWORDS):
            continue
        if pdf.stat().st_size < MIN_FILE_SIZE:
            continue
        if pdf not in all_pdfs:
            all_pdfs.append(pdf)

    # Deduplicate by file hash (some CUSIP folders have the same PDF twice)
    seen_hashes: dict[str, Path] = {}
    unique_pdfs: list[Path] = []
    for pdf in sorted(all_pdfs):
        h = quick_hash(pdf)
        if h not in seen_hashes:
            seen_hashes[h] = pdf
            unique_pdfs.append(pdf)

    return unique_pdfs


def find_all_pdfs() -> list[Path]:
    """Find ALL PDFs in EMMA output, deduped, above minimum size."""
    all_pdfs: list[Path] = []
    pdf_root = _get_pdf_root()
    for pdf in pdf_root.rglob("*.pdf"):
        if pdf.stat().st_size < MIN_FILE_SIZE_ALL:
            continue
        if any(kw in pdf.name for kw in EXCLUDE_KEYWORDS):
            continue
        all_pdfs.append(pdf)

    # Deduplicate
    seen_hashes: dict[str, Path] = {}
    unique_pdfs: list[Path] = []
    for pdf in sorted(all_pdfs):
        h = quick_hash(pdf)
        if h not in seen_hashes:
            seen_hashes[h] = pdf
            unique_pdfs.append(pdf)

    return unique_pdfs


def main_os_only():
    """Original OS-only batch processing."""
    pdfs = find_os_pdfs()
    print(f"Found {len(pdfs)} unique Official Statement PDFs to process:\n")
    for i, p in enumerate(pdfs, 1):
        size_kb = p.stat().st_size / 1024
        print(f"  {i:2d}. [{size_kb:,.0f} KB] {p.parent.name[:12]}.../{p.name[:60]}")

    if "--dry-run" in sys.argv:
        print("\n(dry run - not processing)")
        return

    # Import extraction pipeline
    from src.config import setup_logging
    from src.extraction.orchestrator import ExtractionOrchestrator
    from src.classification.deal_classifier import classify_deal
    from src.storage.json_export import export_deal_to_json
    from src.storage.database import init_database, save_deal_record

    setup_logging()
    orchestrator = ExtractionOrchestrator()
    engine = init_database()

    success = 0
    failed = 0

    for i, pdf_path in enumerate(pdfs, 1):
        print(f"\n{'='*70}")
        print(f"[{i}/{len(pdfs)}] {pdf_path.name}")
        print(f"{'='*70}")
        t0 = time.time()

        try:
            record = orchestrator.extract_document(pdf_path)
            record = classify_deal(record)

            # Export JSON
            json_path = export_deal_to_json(record)
            print(f"  JSON: {json_path.name}")

            # Save to database
            try:
                save_deal_record(engine, record)
                print(f"  DB: saved")
            except Exception as exc:
                print(f"  DB: failed ({exc})", file=sys.stderr)

            elapsed = time.time() - t0
            print(
                f"  Completeness: {record.completeness_score:.0%} | "
                f"Type: {record.primary_classification} | "
                f"Size: {record.size_classification} | "
                f"Time: {elapsed:.1f}s"
            )
            if record.identity.issuer_name:
                print(f"  Issuer: {record.identity.issuer_name}")
            if record.identity.series_name:
                print(f"  Series: {record.identity.series_name}")
            if record.structure.par_amount:
                print(f"  Par: ${record.structure.par_amount:,.0f}")

            success += 1

        except Exception as exc:
            elapsed = time.time() - t0
            print(f"  FAILED ({elapsed:.1f}s): {exc}", file=sys.stderr)
            failed += 1

    print(f"\n{'='*70}")
    print(f"BATCH COMPLETE: {success} succeeded, {failed} failed out of {len(pdfs)}")
    print(f"{'='*70}")


def main_all_types():
    """Multi-module batch processing for all document types."""
    from src.config import setup_logging
    from src.ingestion.pdf_reader import extract_pdf
    from src.modules.registry import get_registry
    from src.storage.database import init_database

    setup_logging()
    registry = get_registry()
    engine = init_database()

    pdfs = find_all_pdfs()
    print(f"Found {len(pdfs)} unique PDFs to process")
    print(f"Registered modules: {', '.join(m.name for m in registry.modules)}\n")

    if "--dry-run" in sys.argv:
        # Show routing only
        route_counts: dict[str, int] = {}
        for i, pdf_path in enumerate(pdfs, 1):
            try:
                ingestion = extract_pdf(pdf_path)
                first_page = ingestion.pages[0].text if ingestion.pages else ""
                mod = registry.route(pdf_path.name, first_page)
                mod_name = mod.display_name if mod else "Official Statement"
            except Exception:
                mod_name = "ERROR"
            route_counts[mod_name] = route_counts.get(mod_name, 0) + 1
            if i <= 50:  # Show first 50
                print(f"  {i:3d}. [{mod_name}] {pdf_path.name[:70]}")

        if len(pdfs) > 50:
            print(f"  ... and {len(pdfs) - 50} more")
        print(f"\nRouting summary:")
        for name, count in sorted(route_counts.items(), key=lambda x: -x[1]):
            print(f"  {name}: {count}")
        return

    # Per-module stats
    module_stats: dict[str, dict[str, int]] = {}
    total_success = 0
    total_failed = 0

    for i, pdf_path in enumerate(pdfs, 1):
        print(f"\n{'='*70}")
        print(f"[{i}/{len(pdfs)}] {pdf_path.name}")
        print(f"{'='*70}")
        t0 = time.time()

        try:
            ingestion = extract_pdf(pdf_path)
            first_page = ingestion.pages[0].text if ingestion.pages else ""
            mod = registry.route(pdf_path.name, first_page)

            if mod is not None:
                print(f"  Module: {mod.display_name}")
                record = mod.extract(ingestion)
                json_path = mod.export_json(record)
                print(f"  JSON: {json_path.name}")

                try:
                    mod.save(engine, record)
                    print(f"  DB: saved")
                except Exception as exc:
                    print(f"  DB: failed ({exc})", file=sys.stderr)

                completeness = getattr(record, "completeness_score", 0)
                issuer = getattr(record, "issuer_name", None) or "Unknown"
                elapsed = time.time() - t0
                print(f"  Completeness: {completeness:.0%} | Issuer: {issuer} | Time: {elapsed:.1f}s")
                mod_name = mod.name
            else:
                # Fall back to OS extractor
                print(f"  Module: Official Statement (default)")
                from src.extraction.orchestrator import ExtractionOrchestrator
                from src.classification.deal_classifier import classify_deal
                from src.storage.json_export import export_deal_to_json
                from src.storage.database import save_deal_record

                orchestrator = ExtractionOrchestrator()
                record = orchestrator.extract_document(pdf_path)
                record = classify_deal(record)
                json_path = export_deal_to_json(record)
                print(f"  JSON: {json_path.name}")

                try:
                    save_deal_record(engine, record)
                    print(f"  DB: saved")
                except Exception as exc:
                    print(f"  DB: failed ({exc})", file=sys.stderr)

                elapsed = time.time() - t0
                print(
                    f"  Completeness: {record.completeness_score:.0%} | "
                    f"Type: {record.primary_classification} | Time: {elapsed:.1f}s"
                )
                mod_name = "official_statement"

            if mod_name not in module_stats:
                module_stats[mod_name] = {"success": 0, "failed": 0}
            module_stats[mod_name]["success"] += 1
            total_success += 1

        except Exception as exc:
            elapsed = time.time() - t0
            print(f"  FAILED ({elapsed:.1f}s): {exc}", file=sys.stderr)
            total_failed += 1

    print(f"\n{'='*70}")
    print(f"BATCH COMPLETE: {total_success} succeeded, {total_failed} failed out of {len(pdfs)}")
    if module_stats:
        print("\nBy module:")
        for mod_name, counts in sorted(module_stats.items(), key=lambda x: -x[1]["success"]):
            print(f"  {mod_name}: {counts['success']} succeeded, {counts['failed']} failed")
    print(f"{'='*70}")


def main():
    if "--all-types" in sys.argv:
        main_all_types()
    else:
        main_os_only()


if __name__ == "__main__":
    main()
