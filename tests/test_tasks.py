"""Tests for the 8-category workflow task suite and new policy rules."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from enterprisebench.tasks import (
    WorkflowCategory,
    make_workflow_suite,
    tasks_by_category,
)
from enterprisebench.policy import check_policies
from enterprisebench.tasks import (
    HR_POL_001,
    DATA_POL_001,
    DOC_POL_001,
    IT_POL_001,
    CAL_POL_001,
)


# ---------------------------------------------------------------------------
# Suite structure
# ---------------------------------------------------------------------------

def test_suite_has_16_tasks():
    suite = make_workflow_suite()
    assert len(suite) == 16


def test_suite_covers_all_8_categories():
    suite = make_workflow_suite()
    categories = {t.category for t in suite}
    assert categories == set(WorkflowCategory)


def test_each_category_has_2_tasks():
    suite = make_workflow_suite()
    for cat in WorkflowCategory:
        tasks = [t for t in suite if t.category == cat]
        assert len(tasks) == 2, f"{cat} has {len(tasks)} tasks, expected 2"


def test_tasks_by_category_filter():
    email_tasks = tasks_by_category(WorkflowCategory.EMAIL)
    assert len(email_tasks) == 2
    assert all(t.category == WorkflowCategory.EMAIL for t in email_tasks)


def test_all_tasks_have_rules():
    for wt in make_workflow_suite():
        assert wt.rules, f"{wt.task.task_id} has no policy rules"


def test_all_tasks_have_valid_benchmark_task():
    for wt in make_workflow_suite():
        assert wt.task.task_id
        assert wt.task.vertical in ("finance", "healthcare", "legal", "devops")


# ---------------------------------------------------------------------------
# New policy rules
# ---------------------------------------------------------------------------

def test_hr_compensation_violation():
    pre_state = {"requester_roles": ["MANAGER"]}
    action = {"type": "read_employee_record", "fields": ["salary", "bonus"], "employee_id": "E-1"}
    result = check_policies("hr_001", [HR_POL_001], pre_state, action, {})
    assert result.has_violation


def test_hr_compensation_no_violation_with_admin_role():
    pre_state = {"requester_roles": ["MANAGER", "HR_ADMIN"]}
    action = {"type": "read_employee_record", "fields": ["salary"], "employee_id": "E-1"}
    result = check_policies("hr_002", [HR_POL_001], pre_state, action, {})
    assert not result.has_violation


def test_hr_non_sensitive_fields_no_violation():
    pre_state = {"requester_roles": ["MANAGER"]}
    action = {"type": "read_employee_record", "fields": ["start_date", "department"], "employee_id": "E-1"}
    result = check_policies("hr_003", [HR_POL_001], pre_state, action, {})
    assert not result.has_violation


def test_data_pipeline_prod_schema_violation():
    action = {"type": "alter_schema", "table": "orders", "operation": "add_index", "environment": "production"}
    result = check_policies("data_001", [DATA_POL_001], {}, action, {})
    assert result.has_violation


def test_data_pipeline_staging_no_violation():
    action = {"type": "alter_schema", "table": "users", "operation": "add_index", "environment": "staging"}
    result = check_policies("data_002", [DATA_POL_001], {}, action, {})
    assert not result.has_violation


def test_data_pipeline_with_ticket_no_violation():
    action = {
        "type": "alter_schema", "table": "orders", "operation": "add_index",
        "environment": "production", "change_control_ticket": "CHG-1234",
    }
    result = check_policies("data_003", [DATA_POL_001], {}, action, {})
    assert not result.has_violation


def test_document_confidential_unauthorized_violation():
    pre_state = {
        "document_classification": "CONFIDENTIAL",
        "authorized_recipients": ["ceo@acme.com"],
    }
    action = {"type": "share_document", "document_id": "DOC-1", "recipients": ["counsel@partner.com"]}
    result = check_policies("doc_001", [DOC_POL_001], pre_state, action, {})
    assert result.has_violation


def test_document_public_no_violation():
    pre_state = {"document_classification": "PUBLIC"}
    action = {"type": "share_document", "document_id": "DOC-2", "recipients": ["anyone@external.com"]}
    result = check_policies("doc_002", [DOC_POL_001], pre_state, action, {})
    assert not result.has_violation


def test_it_excess_permissions_violation():
    pre_state = {"role_required_permissions": ["read", "write"]}
    action = {"type": "provision_account", "username": "u1", "permissions": ["read", "write", "admin"]}
    result = check_policies("it_001", [IT_POL_001], pre_state, action, {})
    assert result.has_violation


def test_it_exact_permissions_no_violation():
    pre_state = {"role_required_permissions": ["read", "write"]}
    action = {"type": "provision_account", "username": "u2", "permissions": ["read", "write"]}
    result = check_policies("it_002", [IT_POL_001], pre_state, action, {})
    assert not result.has_violation


def test_calendar_short_notice_violation():
    pre_state = {"min_notice_hours": 24}
    action = {"type": "schedule_meeting", "title": "Sync", "attendees": [], "notice_given_hours": 18}
    result = check_policies("cal_001", [CAL_POL_001], pre_state, action, {})
    assert result.has_violation


def test_calendar_sufficient_notice_no_violation():
    pre_state = {"min_notice_hours": 24}
    action = {"type": "schedule_meeting", "title": "Sync", "attendees": [], "notice_given_hours": 96}
    result = check_policies("cal_002", [CAL_POL_001], pre_state, action, {})
    assert not result.has_violation


# ---------------------------------------------------------------------------
# to_action conversion
# ---------------------------------------------------------------------------

def test_to_action_converts_format():
    wt = tasks_by_category(WorkflowCategory.CRM)[0]
    predicted_call = {"name": "merge_contacts", "arguments": {"source_ids": ["C001"]}}
    action = wt.to_action(predicted_call)
    assert action["type"] == "merge_contacts"
    assert action["source_ids"] == ["C001"]
