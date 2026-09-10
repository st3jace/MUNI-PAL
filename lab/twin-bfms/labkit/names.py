"""Fictional-name table and whole-phrase collision check (brief rule 10, BUILD-SPEC 3.3).

The table (`scenarios/names/fictional-names.v1.json`) is the ONLY source of party names a
scenario may use. Every value is checked, whole-phrase and case-insensitively, against the
blocklist that `labkit.law` loads from `scenarios/names/blocklist.v1.txt`.

The web / registry collision check is NOT performed here; every entry says so and the run
report prints `web_or_registry: unknown (not performed)`.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from labkit import law

NAME_TABLE_PATH: Path = law.LAB_ROOT / law.NAME_TABLE_FILE_REL
WEB_CHECK_EXPECTED = "not performed"


class NameCollision(ValueError):
    """A name contains a blocklisted phrase (whole-phrase, case-insensitive)."""


class NameNotTabled(ValueError):
    """A party name is not a value of the fictional-name table."""


@lru_cache(maxsize=4)
def load_table(path: Path | None = None) -> dict[str, Any]:
    """Load the name table (cached per path)."""
    table_path = Path(path) if path is not None else NAME_TABLE_PATH
    data = json.loads(table_path.read_text(encoding="utf-8"))
    if not isinstance(data.get("entries"), list) or not data["entries"]:
        raise ValueError(f"name table {table_path} carries no entries")
    return data


def entries(path: Path | None = None) -> list[dict[str, Any]]:
    return list(load_table(path)["entries"])


def table_names(path: Path | None = None) -> frozenset[str]:
    """Every `name` value in the table."""
    return frozenset(str(e["name"]) for e in entries(path))


def collision_check(name: str, *, phrases: tuple[str, ...] | None = None) -> str:
    """Return `name` unchanged or raise `NameCollision` naming every phrase hit."""
    hits = law.blocklist_hits(name, phrases)
    if hits:
        raise NameCollision(f"{name!r} collides with blocklist phrase(s) {hits}")
    return name


def is_tabled(name: str, path: Path | None = None) -> bool:
    return name in table_names(path)


def require_tabled(name: str, path: Path | None = None) -> str:
    """Return `name` if it is a table value AND blocklist-clean; raise otherwise."""
    if not is_tabled(name, path):
        raise NameNotTabled(f"{name!r} is not a value in {law.NAME_TABLE_FILE_REL}")
    return collision_check(name)


def check_table(path: Path | None = None) -> list[str]:
    """Problems with the table itself (empty list == clean).

    Every entry must carry a blocklist-clean name, `collision_checked_against`,
    `check_date` (ISO literal) and `web_collision_check == "not performed"` -- the lab
    never claims a check it did not run.
    """
    problems: list[str] = []
    seen_keys: set[str] = set()
    for entry in entries(path):
        key = str(entry.get("key", ""))
        if not key or key in seen_keys:
            problems.append(f"entry key missing or duplicated: {key!r}")
        seen_keys.add(key)
        name = entry.get("name")
        if not isinstance(name, str) or not name.strip():
            problems.append(f"{key}: name missing")
            continue
        try:
            collision_check(name)
        except NameCollision as exc:
            problems.append(f"{key}: {exc}")
        if not entry.get("collision_checked_against"):
            problems.append(f"{key}: collision_checked_against missing")
        check_date = entry.get("check_date")
        if not isinstance(check_date, str) or not law.ISO_DATE_RE.match(check_date):
            problems.append(f"{key}: check_date must be an ISO literal")
        if entry.get("web_collision_check") != WEB_CHECK_EXPECTED:
            problems.append(f"{key}: web_collision_check must be {WEB_CHECK_EXPECTED!r}")
    if not law.DATA_FILES_PRESENT.get(law.BLOCKLIST_FILE_REL):
        problems.append(f"{law.BLOCKLIST_FILE_REL} absent; blocklist is empty")
    for phrase in law.BLOCKLIST_MIN:
        if phrase not in law.BLOCKLIST_PHRASES:
            problems.append(f"blocklist lacks brief-mandated phrase {phrase!r}")
    return problems


__all__ = [
    "NAME_TABLE_PATH",
    "NameCollision",
    "NameNotTabled",
    "check_table",
    "collision_check",
    "entries",
    "is_tabled",
    "load_table",
    "require_tabled",
    "table_names",
]
