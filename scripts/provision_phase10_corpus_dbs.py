"""
Provision Phase 10 corpus DB files from tracked seed snapshots.

Usage:
    python scripts/provision_phase10_corpus_dbs.py
    python scripts/provision_phase10_corpus_dbs.py --force
"""

from __future__ import annotations

import argparse
import shutil
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ProvisionResult:
    sector: str
    destination: Path
    source: Path
    action: str


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _sector_maps() -> dict[str, tuple[Path, Path]]:
    root = _repo_root() / "emma" / "bond_os_extractor"
    return {
        "waste": (
            root / "data_seed" / "waste" / "corpus.seed.sqlite",
            root / "data" / "waste" / "corpus.db",
        ),
        "healthcare": (
            root / "data_seed" / "healthcare" / "corpus.seed.sqlite",
            root / "data" / "healthcare" / "corpus.db",
        ),
    }


def provision_corpus_dbs(*, force: bool) -> list[ProvisionResult]:
    results: list[ProvisionResult] = []
    for sector, (source, destination) in _sector_maps().items():
        if not source.exists():
            raise FileNotFoundError(
                f"Missing seed snapshot for sector `{sector}`: {source.as_posix()}"
            )
        destination.parent.mkdir(parents=True, exist_ok=True)

        if destination.exists() and not force:
            action = "kept_existing"
        else:
            shutil.copy2(source, destination)
            action = "copied_seed"

        results.append(
            ProvisionResult(
                sector=sector,
                source=source,
                destination=destination,
                action=action,
            )
        )
    return results


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Provision Phase 10 corpus DB files from tracked seed snapshots."
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing corpus DB files with seed snapshots.",
    )
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    results = provision_corpus_dbs(force=bool(args.force))
    for result in results:
        print(
            "[phase10-corpus-provision] "
            f"sector={result.sector} action={result.action} "
            f"source={result.source.as_posix()} "
            f"destination={result.destination.as_posix()}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
