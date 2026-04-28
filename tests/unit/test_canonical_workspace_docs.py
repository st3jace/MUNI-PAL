from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_readme_declares_root_application_tree_is_canonical() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    assert "Canonical application tree" in readme
    assert "Root repository tree" in readme
    assert "src/" in readme
    assert "frontend/" in readme
    assert "tests/" in readme
    assert "contracts/" in readme
    assert "alembic/" in readme


def test_development_policy_archives_v1_and_v2_for_agent_work() -> None:
    policy = (ROOT / "docs/development/CANONICAL_DEV_PATH.md").read_text(encoding="utf-8")

    assert "V1/ is an archived historical application snapshot" in policy
    assert "V2/ is a planning and execution-history workspace" in policy
    assert "Do not implement active application changes under V1/ or V2/" in policy


def test_agent_start_here_points_agents_at_root_tree() -> None:
    start_here = (ROOT / "docs/agent_ops/START_HERE.md").read_text(encoding="utf-8")

    assert "Root repository tree is canonical" in start_here
    assert "Do not edit V1/ or V2/ for active application work" in start_here
