import pytest
from unittest.mock import patch, MagicMock

from remindctl_mcp.server import (
    get_reminders,
    get_lists,
    get_list,
    add_reminder,
    edit_reminder,
    complete_reminder,
    delete_reminder,
    check_status,
)


MOCK_RETURN = {"ok": True}


def make_patch():
    return patch("remindctl_mcp.server.run_remindctl", return_value=MOCK_RETURN)


def test_get_reminders():
    with make_patch() as mock_run:
        result = get_reminders("today")
    mock_run.assert_called_once_with(["today"])
    assert result == MOCK_RETURN


def test_get_lists():
    with make_patch() as mock_run:
        result = get_lists()
    mock_run.assert_called_once_with(["list"])
    assert result == MOCK_RETURN


def test_get_list():
    with make_patch() as mock_run:
        result = get_list("Work")
    mock_run.assert_called_once_with(["list", "Work"])
    assert result == MOCK_RETURN


def test_add_reminder_minimal():
    with make_patch() as mock_run:
        result = add_reminder("Buy milk")
    mock_run.assert_called_once_with(["add", "--title", "Buy milk"])
    assert result == MOCK_RETURN


def test_add_reminder_full():
    with make_patch() as mock_run:
        result = add_reminder("Buy milk", reminder_list="Groceries", due="2026-03-15")
    args = mock_run.call_args[0][0]
    assert args == ["add", "--title", "Buy milk", "--list", "Groceries", "--due", "2026-03-15"]
    assert result == MOCK_RETURN


def test_edit_reminder_title():
    with make_patch() as mock_run:
        result = edit_reminder("42", title="New title")
    mock_run.assert_called_once_with(["edit", "42", "--title", "New title"])
    assert result == MOCK_RETURN


def test_edit_reminder_due():
    with make_patch() as mock_run:
        result = edit_reminder("42", due="2026-04-01")
    mock_run.assert_called_once_with(["edit", "42", "--due", "2026-04-01"])
    assert result == MOCK_RETURN


def test_edit_reminder_no_fields():
    with make_patch():
        with pytest.raises(ValueError, match="At least one of title or due must be provided"):
            edit_reminder("42")


def test_complete_reminder():
    with make_patch() as mock_run:
        result = complete_reminder(["1", "2"])
    mock_run.assert_called_once_with(["complete", "1", "2"])
    assert result == MOCK_RETURN


def test_delete_reminder():
    with make_patch() as mock_run:
        result = delete_reminder("123")
    mock_run.assert_called_once_with(["delete", "123", "--force"])
    assert result == MOCK_RETURN


def test_check_status():
    with make_patch() as mock_run:
        result = check_status()
    mock_run.assert_called_once_with(["status"])
    assert result == MOCK_RETURN


def test_edit_reminder_both_fields():
    with make_patch() as mock_run:
        result = edit_reminder("42", title="New title", due="2026-05-01")
    args = mock_run.call_args[0][0]
    assert "--title" in args
    assert "--due" in args
    assert result == MOCK_RETURN


def test_complete_reminder_empty_list():
    with make_patch() as mock_run:
        result = complete_reminder([])
    mock_run.assert_called_once_with(["complete"])
    assert result == MOCK_RETURN
