"""Run Pareto 4% AI enrichment batch on pre-selected healthcare PDFs.

Reads the list of 116 resolved PDF paths from pareto_paths.txt and
processes each through the full extraction pipeline with AI enabled.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

PATHS_FILE = Path(__file__).parent / "data" / "healthcare" / "analysis" / "pareto_paths.txt"


def main():
    # Set sector FIRST, before any settings access
    from src.config import set_sector, get_settings
    set_sector("healthcare")

    # Ensure AI is ON for this batch
    settings = get_settings()
    settings.tier2_enabled = True

    from src.config import setup_logging
    from src.ingestion.pdf_reader import extract_pdf
    from src.modules.registry import get_registry
    from src.storage.database import init_database

    setup_logging()
    registry = get_registry()
    engine = init_database()

    # Load paths
    paths = [Path(line.strip()) for line in PATHS_FILE.read_text().splitlines() if line.strip()]
    print(f"Pareto 4% batch: {len(paths)} PDFs queued (AI enrichment ON)")
    print(f"Registered modules: {', '.join(m.name for m in registry.modules)}\n")

    # Per-module stats
    module_stats: dict[str, dict[str, int]] = {}
    total_success = 0
    total_failed = 0

    for i, pdf_path in enumerate(paths, 1):
        print(f"\n{'='*70}")
        print(f"[{i}/{len(paths)}] {pdf_path.name[:80]}")
        print(f"{'='*70}")
        t0 = time.time()

        if not pdf_path.exists():
            print(f"  SKIPPED: file not found")
            total_failed += 1
            continue

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
    print(f"PARETO BATCH COMPLETE: {total_success} succeeded, {total_failed} failed out of {len(paths)}")
    if module_stats:
        print("\nBy module:")
        for mod_name, counts in sorted(module_stats.items(), key=lambda x: -x[1]["success"]):
            print(f"  {mod_name}: {counts['success']} succeeded, {counts['failed']} failed")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
