"""
Cleanup script: delete PDFs that have been fully processed or are redundant.

Targets:
  1. Waste sector: PDFs with extraction completeness >= 50% OR event/rating-only docs
  2. Healthcare sector: same criteria
  3. Healthcare v1 archive: entire directory (superseded by v2 crawl)

Usage:
  python scripts/cleanup_processed_pdfs.py --dry-run    # Show what would be deleted
  python scripts/cleanup_processed_pdfs.py --execute     # Actually delete
"""

import argparse
import os
import shutil
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EMMA = ROOT / "emma"
CRAWLER_OUT = EMMA / "emma_crawler" / "output"
EXTRACTOR = EMMA / "bond_os_extractor"


def get_deletable_pdfs(sector: str) -> list[tuple[str, str]]:
    """Return list of (full_path, reason) for PDFs safe to delete in a sector."""
    db_path = EXTRACTOR / "data" / sector / "corpus.db"
    pdfs_dir = CRAWLER_OUT / sector / "pdfs"

    if not db_path.exists():
        print(f"  WARNING: {db_path} not found, skipping {sector}")
        return []

    conn = sqlite3.connect(str(db_path))
    c = conn.cursor()

    # Build per-file extraction summary from document_index
    c.execute(
        "SELECT source_file, doc_type, completeness_score FROM document_index"
    )
    file_info: dict[str, dict] = {}
    for sf, dt, cs in c.fetchall():
        if sf not in file_info:
            file_info[sf] = {"types": set(), "max_completeness": 0.0}
        file_info[sf]["types"].add(dt)
        if cs and cs > file_info[sf]["max_completeness"]:
            file_info[sf]["max_completeness"] = cs

    # Also include OS-only documents table
    c.execute("SELECT source_file, completeness_score FROM documents")
    for sf, cs in c.fetchall():
        if sf not in file_info:
            file_info[sf] = {"types": {"official_statement"}, "max_completeness": cs or 0.0}
        else:
            if cs and cs > file_info[sf]["max_completeness"]:
                file_info[sf]["max_completeness"] = cs

    conn.close()

    deletable = []
    for sf, info in file_info.items():
        types = info["types"]
        mc = info["max_completeness"]

        # Determine if this file is safe to delete
        reason = None
        if mc >= 0.5:
            reason = f"well-extracted ({mc:.0%} completeness)"
        elif types <= {"event_filing", "rating_action"}:
            # Event filings and rating actions are structurally simple —
            # if they appear in the DB, extraction is complete
            reason = f"event/rating doc (fully extracted, {'/'.join(sorted(types))})"

        if reason is None:
            continue

        # Resolve full path
        cusip = sf.split("_")[0] if "_" in sf else ""
        full_path = pdfs_dir / cusip / sf
        if full_path.exists():
            deletable.append((str(full_path), reason))

    return deletable


def run(dry_run: bool):
    total_bytes = 0
    total_files = 0
    all_targets: list[tuple[str, str]] = []

    # --- Sector processed PDFs ---
    for sector in ["waste", "healthcare"]:
        print(f"\n{'='*60}")
        print(f"  {sector.upper()} — processed PDFs")
        print(f"{'='*60}")
        targets = get_deletable_pdfs(sector)
        sector_bytes = sum(os.path.getsize(p) for p, _ in targets)
        print(f"  Files to delete: {len(targets)}")
        print(f"  Space to reclaim: {sector_bytes / (1024**3):.2f} GB")
        if targets:
            # Show sample
            for p, r in targets[:5]:
                fname = os.path.basename(p)
                print(f"    {fname[:60]}... — {r}")
            if len(targets) > 5:
                print(f"    ... and {len(targets) - 5} more")
        all_targets.extend(targets)
        total_bytes += sector_bytes
        total_files += len(targets)

    # --- Healthcare v1 archive ---
    archive_dir = CRAWLER_OUT / "_archive" / "healthcare_v1"
    print(f"\n{'='*60}")
    print(f"  HEALTHCARE v1 ARCHIVE — entire directory")
    print(f"{'='*60}")
    if archive_dir.exists():
        archive_bytes = 0
        archive_files = 0
        for root, dirs, files in os.walk(str(archive_dir)):
            for f in files:
                fp = os.path.join(root, f)
                archive_bytes += os.path.getsize(fp)
                archive_files += 1
        print(f"  Files to delete: {archive_files}")
        print(f"  Space to reclaim: {archive_bytes / (1024**3):.2f} GB")
        total_bytes += archive_bytes
        total_files += archive_files
    else:
        print("  Archive directory not found, skipping")
        archive_dir = None

    # --- Summary ---
    print(f"\n{'='*60}")
    print(f"  TOTAL")
    print(f"{'='*60}")
    print(f"  Files: {total_files:,}")
    print(f"  Space: {total_bytes / (1024**3):.2f} GB")

    if dry_run:
        print(f"\n  ** DRY RUN — nothing was deleted **")
        print(f"  Re-run with --execute to delete.")
        return

    # --- Execute deletions ---
    print(f"\n  Executing deletions...")

    deleted_files = 0
    deleted_bytes = 0

    # Delete individual processed PDFs
    for path, reason in all_targets:
        try:
            size = os.path.getsize(path)
            os.remove(path)
            deleted_files += 1
            deleted_bytes += size
        except OSError as e:
            print(f"  ERROR deleting {path}: {e}")

    # Clean up empty CUSIP directories (skip on permission errors — OneDrive may lock)
    for sector in ["waste", "healthcare"]:
        pdfs_dir = CRAWLER_OUT / sector / "pdfs"
        if pdfs_dir.exists():
            for cusip_dir in pdfs_dir.iterdir():
                try:
                    if cusip_dir.is_dir() and not any(cusip_dir.iterdir()):
                        cusip_dir.rmdir()
                        print(f"  Removed empty dir: {cusip_dir.name}")
                except OSError:
                    pass  # OneDrive sync may hold locks

    # Delete archive directory
    if archive_dir and archive_dir.exists():
        archive_size = 0
        archive_count = 0
        # First pass: delete all files
        for root, dirs, files in os.walk(str(archive_dir)):
            for f in files:
                fp = os.path.join(root, f)
                try:
                    sz = os.path.getsize(fp)
                    os.chmod(fp, 0o777)  # ensure writable
                    os.remove(fp)
                    archive_size += sz
                    archive_count += 1
                except OSError as e:
                    print(f"  WARN: could not delete {fp}: {e}")
        print(f"  Deleted {archive_count} archive files ({archive_size / (1024**3):.2f} GB)")
        deleted_files += archive_count
        deleted_bytes += archive_size
        # Second pass: remove empty directories bottom-up
        def _onerror(func, path, exc_info):
            """Handle permission errors on Windows/OneDrive by forcing writable."""
            import stat
            os.chmod(path, stat.S_IWRITE)
            func(path)
        try:
            shutil.rmtree(str(archive_dir), onexc=_onerror)
            print(f"  Removed archive directory: {archive_dir}")
        except OSError:
            print(f"  WARN: archive files deleted but empty dirs may remain (OneDrive lock)")

    print(f"\n  DONE: {deleted_files:,} files deleted, {deleted_bytes / (1024**3):.2f} GB reclaimed")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Clean up processed/redundant PDFs")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--dry-run", action="store_true", help="Show what would be deleted")
    group.add_argument("--execute", action="store_true", help="Actually delete files")
    args = parser.parse_args()

    run(dry_run=args.dry_run)
