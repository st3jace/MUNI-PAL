"""Fence: fictional-name table + whole-phrase blocklist (brief rule 10, BUILD-SPEC 3.3, 6).

The twelve old-pack city names are never spelled here: they are the purely alphabetic
fragments of the `[sources]` section of the forbidden-token data file (after unwrapping
the one-character no-op class each fragment ends in), and the test checks that each of
them is also a blocklist phrase. The brief rule-10 minimum list IS spelled here (this file
already carries real names as negative cases); `law.BLOCKLIST_MIN` is loaded from the data
file so no lab `.py` spells a real name.
"""

from __future__ import annotations

import re

import pytest

from tests import lab_support

LAB = lab_support.LAB_ROOT
_ALPHA = re.compile(r"^[A-Za-z]+$")
#: COS working paper 2026-09-10 (LAB-BRIEF.md) section 4 rule 10 + the real-issuer phrases.
BRIEF_RULE_10_MIN: tuple[str, ...] = (
    "Deloitte",
    "KPMG",
    "EY",
    "PwC",
    "Baird",
    "Ice Miller",
    "UMB",
    "Kuhn Loeb",
    "Piper Sandler",
    "Stifel",
    "Raymond James",
    "Choice Advisors",
    "Greenberg Traurig",
    "Kutak Rock",
    "Squire Patton",
    "Orrick",
    "Chapman and Cutler",
    "Gust Rosenfeld",
    "Slania",
    "American Leadership Academy",
    "Sierra Vista",
    "Pima",
    "Phoenix IDA",
    "Arizona Finance Authority",
    "City of Sierra Vista",
    "County of Pima",
    "AZIDA",
    "Kuhn Loeb Inc",
    "Deloitte & Touche LLP",
)


def test_lab_blocklist_complete_and_names_clean() -> None:
    lab_support.import_labkit()
    from labkit import law, names, scenario

    assert law.DATA_FILES_PRESENT.get(law.BLOCKLIST_FILE_REL) is True
    missing = [p for p in BRIEF_RULE_10_MIN if p not in law.BLOCKLIST_PHRASES]
    assert missing == [], f"blocklist lacks brief-mandated phrase(s): {missing}"
    assert set(law.BLOCKLIST_MIN) == set(law.BLOCKLIST_PHRASES), "BLOCKLIST_MIN must be loaded from the data file"
    assert set(BRIEF_RULE_10_MIN) <= set(law.BLOCKLIST_MIN)
    cities = [law.deobfuscate_fragment(frag) for frag in law.FORBIDDEN_SOURCES]
    cities = [c for c in cities if _ALPHA.match(c)]
    assert len(cities) == 12, f"expected the twelve old-pack city names in [sources], found {len(cities)}"
    assert [c for c in cities if c not in law.BLOCKLIST_PHRASES] == []

    assert names.check_table() == []
    entries = names.entries()
    assert len(entries) >= 10
    for entry in entries:
        assert entry["web_collision_check"] == names.WEB_CHECK_EXPECTED
        assert entry["collision_checked_against"]
        assert names.collision_check(entry["name"]) == entry["name"]

    for deal_id in ("SYN-HSG-AZ-2025-LAB01", "SYN-HSG-AZ-2025-LAB02", "SYN-HSG-AZ-2025-LAB03"):
        sc = scenario.load(LAB / "scenarios" / f"{deal_id}.synthetic.json")
        for party in sc.data["parties"]:
            if party.get("name") is None:
                assert party.get("status") == "unrated"
                continue
            assert names.require_tabled(party["name"]) == party["name"]
        assert names.require_tabled(sc.data["obligated_person"]["name"])

    with pytest.raises(names.NameCollision):
        names.collision_check("Deloitte & Touche LLP")
    with pytest.raises(names.NameCollision):
        names.collision_check("Sierra Vista IDA")
    with pytest.raises(names.NameCollision):
        names.collision_check("piper sandler & co")
    assert names.collision_check("Creosote & Mesa LLP") == "Creosote & Mesa LLP"
    assert names.collision_check("Pimaville Holdings") == "Pimaville Holdings"  # whole-phrase, not substring
    with pytest.raises(names.NameNotTabled):
        names.require_tabled("Mesa Verde Capital Partners LLC")
