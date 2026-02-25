from scripts.assess_test_suite_health import parse_collected_nodeids


def test_parse_collected_nodeids_extracts_pytest_node_ids() -> None:
    stdout = """
tests/integration/test_readiness_api.py::test_readiness_ok
tests\\unit\\test_fact_service.py::test_fact_merge

=========================== 2 tests collected in 0.04s ===========================
"""
    nodeids = parse_collected_nodeids(stdout)
    assert nodeids == [
        "tests/integration/test_readiness_api.py::test_readiness_ok",
        "tests/unit/test_fact_service.py::test_fact_merge",
    ]


def test_parse_collected_nodeids_ignores_non_node_lines() -> None:
    stdout = """
============================= test session starts ==============================
platform win32 -- Python 3.14
collected 0 items
"""
    assert parse_collected_nodeids(stdout) == []
