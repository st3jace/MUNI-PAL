"""Regression tests for DMS/VDR scope documentation drift."""

import ast
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PLAN = ROOT / "PLAN.md"
DMS_MODELS = ROOT / "src/munipal/core/models/deal_document.py"
DMS_MIGRATION = (
    ROOT
    / "alembic/versions/20260226_0001_g7h8i9j0k1l2_add_document_management_system.py"
)


def _plan_table_names() -> list[str]:
    names: list[str] = []
    marker = chr(96)
    pattern = r"\| " + marker + r"([^" + marker + r"]+)" + marker + r" \|"
    in_models_table = False
    for line in PLAN.read_text().splitlines():
        if line.startswith("### New Models"):
            in_models_table = True
            continue
        if in_models_table and line.startswith("### Modifications"):
            break
        if not in_models_table:
            continue
        match = re.match(pattern, line)
        if match:
            names.append(match.group(1))
    return names


def _declared_plan_counts() -> list[int]:
    text = PLAN.read_text()
    return [
        int(match.group(1))
        for match in re.finditer(r"(?:Schema \(|creates all )(\d+) (?:new )?tables", text)
    ]


def _model_table_names() -> list[str]:
    module = ast.parse(DMS_MODELS.read_text())
    names: list[str] = []
    for node in module.body:
        if isinstance(node, ast.ClassDef):
            for stmt in node.body:
                if (
                    isinstance(stmt, ast.Assign)
                    and any(
                        isinstance(target, ast.Name) and target.id == "__tablename__"
                        for target in stmt.targets
                    )
                    and isinstance(stmt.value, ast.Constant)
                    and isinstance(stmt.value.value, str)
                ):
                    names.append(stmt.value.value)
    return names


def _migration_table_names() -> list[str]:
    names: list[str] = []
    lines = DMS_MIGRATION.read_text().splitlines()
    for idx, line in enumerate(lines):
        if "op.create_table(" in line:
            names.append(lines[idx + 1].strip().rstrip(",").strip(chr(34)).strip(chr(39)))
    return names


def test_plan_dms_table_count_matches_listed_scope():
    table_names = _plan_table_names()

    assert len(table_names) == 12
    assert _declared_plan_counts() == [12, 12]


def test_plan_dms_scope_matches_models_and_migration():
    plan_names = _plan_table_names()

    assert set(plan_names) == set(_model_table_names())
    assert set(plan_names) == set(_migration_table_names())


def test_plan_marks_deferred_dms_tables_explicitly():
    text = PLAN.read_text()

    assert "### Deferred DMS/VDR Tables" in text
    assert "not part of this migration" in text
