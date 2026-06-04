import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from enterprisebench.data import make_task, make_suite, make_multi_turn_task, TASK_TEMPLATES
from enterprisebench.core import VERTICALS


def test_make_task_returns_benchmark_task():
    task = make_task(vertical="finance")
    assert task.vertical == "finance"
    assert task.expected_call["name"] == "get_stock_price"


def test_make_suite_length():
    suite = make_suite(n=12)
    assert len(suite) == 12


def test_make_suite_covers_all_verticals():
    suite = make_suite(n=20)
    verticals_seen = {t.vertical for t in suite}
    assert verticals_seen == set(VERTICALS)


def test_task_templates_have_three_plus_per_vertical():
    for vertical in VERTICALS:
        assert len(TASK_TEMPLATES[vertical]) >= 3


def test_make_multi_turn_task():
    task = make_multi_turn_task(vertical="finance")
    assert task.is_multi_turn
    assert len(task.turns) >= 2


def test_make_multi_turn_task_devops():
    task = make_multi_turn_task(vertical="devops")
    assert task.is_multi_turn
    for turn in task.turns:
        assert "instruction" in turn
        assert "expected_call" in turn
