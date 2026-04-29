from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "docs/development/VERIFICATION_COMMANDS.md"


def test_verification_commands_doc_covers_backend_frontend_and_contracts() -> None:
    doc = DOC.read_text(encoding="utf-8")

    assert "/home/st3ja/.local/bin/uv run --extra dev pytest" in doc
    assert "cd frontend" in doc
    assert "npm install" in doc
    assert "npm run test" in doc
    assert "npm run lint" in doc
    assert "npm run build" in doc
    assert "tests/contract" in doc
    assert "contracts/openapi.v1.json" in doc


def test_readme_and_agent_start_here_point_to_verification_commands() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    start_here = (ROOT / "docs/agent_ops/START_HERE.md").read_text(encoding="utf-8")

    assert "docs/development/VERIFICATION_COMMANDS.md" in readme
    assert "docs/development/VERIFICATION_COMMANDS.md" in start_here
