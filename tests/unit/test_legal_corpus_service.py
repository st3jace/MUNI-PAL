import json
from pathlib import Path

from munipal.services.legal_corpus_service import LegalCorpusService


def test_recommend_document_classes_uses_document_type_and_features(tmp_path: Path):
    catalog_path = tmp_path / "catalog.json"
    catalog_path.write_text(
        json.dumps(
            {
                "document_classes": [
                    {"class_name": "loan_agreement", "count": 120, "sample_files": ["a.pdf"]},
                    {"class_name": "credit_agreement", "count": 80, "sample_files": ["b.pdf"]},
                ]
            }
        ),
        encoding="utf-8",
    )

    service = LegalCorpusService(catalog_path=str(catalog_path))
    recs = service.recommend_document_classes(
        document_type_code="loan_agreement",
        deal_features=["cross_default"],
        limit=5,
    )

    assert service.has_catalog() is True
    assert recs
    assert recs[0]["class_name"] in {"loan_agreement", "credit_agreement"}
    assert any("document_type:loan_agreement" in reason for reason in recs[0]["reasons"])


def test_recommend_document_classes_without_catalog_still_returns_structure(tmp_path: Path):
    service = LegalCorpusService(catalog_path=str(tmp_path / "missing.json"))
    recs = service.recommend_document_classes(
        document_type_code="trust_indenture",
        deal_features=["additional_bonds_test"],
        limit=3,
    )

    assert service.has_catalog() is False
    assert recs
    assert all("class_name" in item for item in recs)
