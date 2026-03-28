import json
from pathlib import Path

from scripts.build_legal_template_catalog import build_catalog


def test_build_catalog_generates_latest_artifacts(tmp_path: Path):
    pdf_root = tmp_path / "output"
    output_dir = tmp_path / "reports"

    (pdf_root / "waste" / "pdfs" / "A1").mkdir(parents=True)
    (pdf_root / "healthcare" / "pdfs" / "B1").mkdir(parents=True)

    # Intentionally minimal/invalid PDF bytes to exercise parse-error handling path.
    (pdf_root / "waste" / "pdfs" / "A1" / "Loan_Agreement_1.pdf").write_bytes(b"not-a-pdf")
    (pdf_root / "healthcare" / "pdfs" / "B1" / "Official_Statement_1.pdf").write_bytes(
        b"not-a-pdf"
    )

    result = build_catalog(
        pdf_root=pdf_root,
        output_dir=output_dir,
        max_pdfs=0,
        text_pages=1,
        text_samples_per_class=2,
        min_unmapped_count=1,
    )

    latest_json = output_dir / "legal_template_catalog_latest.json"
    latest_md = output_dir / "legal_template_catalog_latest.md"

    assert result.json_path.exists()
    assert result.markdown_path.exists()
    assert latest_json.exists()
    assert latest_md.exists()

    payload = json.loads(latest_json.read_text(encoding="utf-8"))
    assert payload["summary"]["total_pdfs_scanned"] == 2
    assert "document_classes" in payload
    assert any(item["class_name"] == "loan_agreement" for item in payload["document_classes"])
