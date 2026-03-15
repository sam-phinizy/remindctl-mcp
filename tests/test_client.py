import json
from unittest.mock import AsyncMock, patch

import pytest

from apple_reminders.client import AsyncRemindersClient
from apple_reminders.models import AuthStatus, Reminder, ReminderList


REMINDER_JSON = {
    "dueDate": "2026-03-15T04:00:00Z",
    "id": "abc123",
    "isCompleted": False,
    "listID": "list1",
    "listName": "Reminders",
    "priority": "none",
    "title": "Test reminder",
}

LIST_JSON = {
    "id": "list1",
    "overdueCount": 0,
    "reminderCount": 5,
    "title": "Reminders",
}

STATUS_JSON = {"authorized": True, "status": "full-access"}


@pytest.fixture
def client():
    return AsyncRemindersClient()


@pytest.fixture
def mock_run():
    with patch("apple_reminders.client.run_remindctl", new_callable=AsyncMock) as m:
        yield m


@pytest.mark.asyncio
async def test_show(client, mock_run):
    mock_run.return_value = [REMINDER_JSON]
    result = await client.show("today")
    mock_run.assert_called_once_with(["show", "today"])
    assert len(result) == 1
    assert isinstance(result[0], Reminder)
    assert result[0].title == "Test reminder"


@pytest.mark.asyncio
async def test_show_with_list(client, mock_run):
    mock_run.return_value = [REMINDER_JSON]
    await client.show("today", list="Work")
    mock_run.assert_called_once_with(["show", "today", "--list", "Work"])


@pytest.mark.asyncio
async def test_add(client, mock_run):
    mock_run.return_value = REMINDER_JSON
    result = await client.add("Test reminder")
    mock_run.assert_called_once_with(["add", "--title", "Test reminder"])
    assert isinstance(result, Reminder)


@pytest.mark.asyncio
async def test_add_full(client, mock_run):
    mock_run.return_value = REMINDER_JSON
    await client.add("Test", list="Work", due="tomorrow", notes="note", priority="high")
    mock_run.assert_called_once_with([
        "add", "--title", "Test", "--list", "Work",
        "--due", "tomorrow", "--notes", "note", "--priority", "high",
    ])


@pytest.mark.asyncio
async def test_edit(client, mock_run):
    mock_run.return_value = REMINDER_JSON
    result = await client.edit("abc123", title="New title")
    mock_run.assert_called_once_with(["edit", "abc123", "--title", "New title"])
    assert isinstance(result, Reminder)


@pytest.mark.asyncio
async def test_edit_no_fields(client):
    with pytest.raises(ValueError, match="At least one field"):
        await client.edit("abc123")


@pytest.mark.asyncio
async def test_edit_clear_due(client, mock_run):
    mock_run.return_value = REMINDER_JSON
    await client.edit("abc123", clear_due=True)
    mock_run.assert_called_once_with(["edit", "abc123", "--clear-due"])


@pytest.mark.asyncio
async def test_complete(client, mock_run):
    mock_run.return_value = [REMINDER_JSON]
    result = await client.complete(["abc123"])
    mock_run.assert_called_once_with(["complete", "abc123"])
    assert isinstance(result[0], Reminder)


@pytest.mark.asyncio
async def test_uncomplete(client, mock_run):
    mock_run.return_value = REMINDER_JSON
    result = await client.uncomplete("abc123")
    mock_run.assert_called_once_with(["edit", "abc123", "--incomplete"])
    assert isinstance(result, Reminder)


@pytest.mark.asyncio
async def test_delete(client, mock_run):
    mock_run.return_value = {"deleted": True}
    result = await client.delete("abc123")
    mock_run.assert_called_once_with(["delete", "abc123", "--force"])


@pytest.mark.asyncio
async def test_lists(client, mock_run):
    mock_run.return_value = [LIST_JSON]
    result = await client.lists()
    mock_run.assert_called_once_with(["list"])
    assert isinstance(result[0], ReminderList)


@pytest.mark.asyncio
async def test_get_list(client, mock_run):
    mock_run.return_value = [REMINDER_JSON]
    result = await client.get_list("Work")
    mock_run.assert_called_once_with(["list", "Work"])
    assert isinstance(result[0], Reminder)


@pytest.mark.asyncio
async def test_create_list(client, mock_run):
    mock_run.return_value = LIST_JSON
    result = await client.create_list("New List")
    mock_run.assert_called_once_with(["list", "New List", "--create"])
    assert isinstance(result, ReminderList)


@pytest.mark.asyncio
async def test_rename_list(client, mock_run):
    mock_run.return_value = LIST_JSON
    result = await client.rename_list("Old", "New")
    mock_run.assert_called_once_with(["list", "Old", "--rename", "New"])
    assert isinstance(result, ReminderList)


@pytest.mark.asyncio
async def test_delete_list(client, mock_run):
    mock_run.return_value = {"deleted": True}
    await client.delete_list("Old", force=True)
    mock_run.assert_called_once_with(["list", "Old", "--delete", "--force"])


@pytest.mark.asyncio
async def test_delete_list_no_force(client, mock_run):
    mock_run.return_value = {"deleted": True}
    await client.delete_list("Old")
    mock_run.assert_called_once_with(["list", "Old", "--delete"])


@pytest.mark.asyncio
async def test_status(client, mock_run):
    mock_run.return_value = STATUS_JSON
    result = await client.status()
    mock_run.assert_called_once_with(["status"])
    assert isinstance(result, AuthStatus)
    assert result.authorized is True
