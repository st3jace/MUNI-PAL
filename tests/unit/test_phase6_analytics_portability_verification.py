from scripts.verify_phase6_analytics_portability import (
    PathFinding,
    is_allowlisted,
    scan_line_for_findings,
)


def test_scan_line_detects_windows_drive_path() -> None:
    findings = scan_line_for_findings(
        line='path = "C:\\\\Users\\\\analyst\\\\data\\\\file.csv"',
        line_number=12,
        relative_file="emma/bond_os_extractor/src/example.py",
    )
    assert any(item.rule_id == "windows_drive_path" for item in findings)


def test_scan_line_ignores_sqlite_connection_url() -> None:
    findings = scan_line_for_findings(
        line='engine = create_engine(f"sqlite:///{db_path}", echo=False)',
        line_number=8,
        relative_file="emma/bond_os_extractor/src/storage/database.py",
    )
    assert findings == []


def test_scan_line_detects_unix_and_onedrive_paths() -> None:
    unix_findings = scan_line_for_findings(
        line='base_dir = "/home/user/analytics/cache"',
        line_number=3,
        relative_file="emma/bond_os_extractor/src/example.py",
    )
    onedrive_findings = scan_line_for_findings(
        line='backup = "OneDrive\\\\MEGA\\\\PROJECTS"',
        line_number=4,
        relative_file="emma/bond_os_extractor/src/example.py",
    )
    assert any(item.rule_id == "unix_machine_path" for item in unix_findings)
    assert any(item.rule_id == "onedrive_path" for item in onedrive_findings)


def test_allowlist_matches_known_legacy_data_loader_path() -> None:
    finding = PathFinding(
        file="emma/bond_os_extractor/src/analysis/data_loader.py",
        line=31,
        rule_id="windows_drive_path",
        snippet=r'r"C:\Users\st3ja\OneDrive\Documents\PROJECTS\AZRFO\QF\WTE\waste_tickers"',
    )
    assert is_allowlisted(finding) is True


def test_allowlist_does_not_match_other_paths() -> None:
    finding = PathFinding(
        file="emma/bond_os_extractor/src/example.py",
        line=9,
        rule_id="windows_drive_path",
        snippet=r'path = "C:\Users\analyst\data\file.csv"',
    )
    assert is_allowlisted(finding) is False
