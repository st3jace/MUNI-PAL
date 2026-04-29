from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "docs/architecture/BFMS_DATA_MODEL_PRIMITIVES.md"


def test_model_to_primitive_mapping_names_all_core_primitives() -> None:
    doc = DOC.read_text(encoding="utf-8")

    for primitive in [
        "Project",
        "Playbook",
        "Artifact",
        "Chunk",
        "ExtractionJob",
        "ExtractedFact",
        "Accepted fact",
        "Deliverable",
        "Warm Handoff Pack",
    ]:
        assert primitive in doc


def test_mapping_calls_out_required_platform_fields_and_gaps() -> None:
    doc = DOC.read_text(encoding="utf-8")

    for required_phrase in [
        "Tenant fields",
        "Sector fields",
        "Provenance fields",
        "Review-state fields",
        "Audit fields",
        "Migration gaps",
        "Duplicated or overlapping fields",
        "Missing fields",
    ]:
        assert required_phrase in doc


def test_mapping_links_primitives_to_implemented_models_and_migrations() -> None:
    doc = DOC.read_text(encoding="utf-8")

    for evidence in [
        "src/munipal/core/models/project.py",
        "src/munipal/core/models/playbook.py",
        "src/munipal/core/models/artifact.py",
        "src/munipal/core/models/extraction.py",
        "src/munipal/core/models/fact.py",
        "src/munipal/core/models/deliverable.py",
        "alembic/versions/20260127_0001_a1b2c3d4e5f6_initial_schema.py",
        "alembic/versions/20260220_0001_b8c9d0e1f2a3_add_project_tenant_id.py",
    ]:
        assert evidence in doc
