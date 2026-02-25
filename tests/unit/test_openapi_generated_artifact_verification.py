from pathlib import Path

from scripts.verify_openapi_generated_artifacts import (
    compare_directories,
    compare_text_files,
)


def test_compare_text_files_normalizes_newlines(tmp_path: Path) -> None:
    expected = tmp_path / "expected.ts"
    generated = tmp_path / "generated.ts"
    expected.write_bytes(b"line1\nline2\n")
    generated.write_bytes(b"line1\r\nline2\r\n")

    mismatches = compare_text_files(expected, generated, label="types")
    assert mismatches == []


def test_compare_directories_reports_missing_extra_and_changed(tmp_path: Path) -> None:
    expected_root = tmp_path / "expected"
    generated_root = tmp_path / "generated"
    expected_root.mkdir()
    generated_root.mkdir()

    (expected_root / "A.ts").write_text("same\n", encoding="utf-8")
    (expected_root / "B.ts").write_text("expected\n", encoding="utf-8")
    (generated_root / "A.ts").write_text("same\n", encoding="utf-8")
    (generated_root / "B.ts").write_text("different\n", encoding="utf-8")
    (generated_root / "C.ts").write_text("extra\n", encoding="utf-8")

    mismatches = compare_directories(expected_root, generated_root, label="client")
    assert any("unexpected generated file: C.ts" in item for item in mismatches)
    assert any("content differs: B.ts" in item for item in mismatches)
