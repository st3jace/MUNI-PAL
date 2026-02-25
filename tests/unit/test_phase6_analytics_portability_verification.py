from scripts.verify_phase6_analytics_portability import scan_line_for_findings


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

