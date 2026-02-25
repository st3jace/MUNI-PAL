from datetime import datetime

import pytest

from scripts.dispatch_github_workflow import (
    _parse_github_time,
    _parse_inputs,
    _parse_owner_repo,
)


def test_parse_owner_repo_supports_https_remote() -> None:
    owner, repo = _parse_owner_repo("https://github.com/st3jace/MUNI-PAL.git")
    assert owner == "st3jace"
    assert repo == "MUNI-PAL"


def test_parse_owner_repo_supports_ssh_remote() -> None:
    owner, repo = _parse_owner_repo("git@github.com:st3jace/MUNI-PAL.git")
    assert owner == "st3jace"
    assert repo == "MUNI-PAL"


def test_parse_inputs_supports_multiple_values() -> None:
    parsed = _parse_inputs(["note=phase10", "week=2026-W09"])
    assert parsed == {"note": "phase10", "week": "2026-W09"}


def test_parse_inputs_rejects_invalid_pairs() -> None:
    with pytest.raises(ValueError):
        _parse_inputs(["invalid"])


def test_parse_github_time_accepts_zulu_suffix() -> None:
    parsed = _parse_github_time("2026-02-25T16:30:00Z")
    assert isinstance(parsed, datetime)
    assert parsed.isoformat() == "2026-02-25T16:30:00+00:00"
