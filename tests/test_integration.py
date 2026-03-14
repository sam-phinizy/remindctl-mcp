import os
import shutil

import pytest

if shutil.which("remindctl") is None:
    pytest.skip("remindctl not installed", allow_module_level=True)

from remindctl_mcp.server import (
    add_reminder,
    check_status,
    complete_reminder,
    delete_reminder,
    edit_reminder,
    get_lists,
    get_reminders,
)


# ---------------------------------------------------------------------------
# Read-only tests — always run when the binary is present
# ---------------------------------------------------------------------------


def test_check_status():
    result = check_status()
    assert isinstance(result, dict)


def test_get_lists():
    result = get_lists()
    assert isinstance(result, list)


def test_get_reminders_today():
    result = get_reminders("today")
    assert isinstance(result, list)


def test_get_reminders_all():
    result = get_reminders("all")
    assert isinstance(result, list)


# ---------------------------------------------------------------------------
# Mutation tests — opt-in via REMINDCTL_TEST_LIST env var
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def test_list_name():
    name = os.environ.get("REMINDCTL_TEST_LIST")
    if not name:
        pytest.skip("Set REMINDCTL_TEST_LIST to run mutation tests")
    return name


def test_add_and_delete_reminder(test_list_name):
    result = add_reminder(title="Integration test reminder", reminder_list=test_list_name)
    assert isinstance(result, dict)
    assert "id" in result or "title" in result
    reminder_id = result["id"]
    delete_reminder(reminder_id)


def test_add_and_complete_reminder(test_list_name):
    result = add_reminder(title="Integration test complete", reminder_list=test_list_name)
    assert isinstance(result, dict)
    reminder_id = result["id"]
    complete_result = complete_reminder([reminder_id])
    assert complete_result is not None


def test_edit_reminder(test_list_name):
    result = add_reminder(title="Integration test edit original", reminder_list=test_list_name)
    assert isinstance(result, dict)
    reminder_id = result["id"]
    edit_result = edit_reminder(reminder_id, title="Integration test edit updated")
    assert edit_result is not None
    delete_reminder(reminder_id)
