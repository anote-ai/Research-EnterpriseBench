import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from enterprisebench.core import BenchmarkTask, VERTICALS
from enterprisebench.data import make_task, make_suite


def test_make_task_returns_benchmark_task():
    task = make_task(vertical="finance")
    assert isinstance(task, BenchmarkTask)


def test_make_suite_returns_20_items():
    suite = make_suite(20)
    assert len(suite) == 20


def test_all_verticals_in_suite():
    suite = make_suite(20)
    found_verticals = {t.vertical for t in suite}
    assert found_verticals == set(VERTICALS)


def test_make_suite_deterministic():
    s1 = make_suite(10, seed=99)
    s2 = make_suite(10, seed=99)
    assert [t.task_id for t in s1] == [t.task_id for t in s2]


def test_task_tool_schema_has_name_and_parameters():
    task = make_task(vertical="legal")
    assert "name" in task.tool_schema
    assert "parameters" in task.tool_schema
