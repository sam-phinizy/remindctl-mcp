from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from apple_reminders.models import AuthStatus, Reminder, ReminderList


REMINDER_JSON = {
    "dueDate": "2026-03-15T04:00:00Z",
    "id": "abc123",
    "isCompleted": False,
    "listID": "list1",
    "listName": "Reminders",
    "priority": "none",
    "title": "Test",
}

LIST_JSON = {"id": "list1", "overdueCount": 0, "reminderCount": 5, "title": "Reminders"}
STATUS_JSON = {"authorized": True, "status": "full-access"}


@pytest.fixture
def mock_client():
    with patch("apple_reminders.mcp.server.client") as m:
        yield m


@pytest.mark.asyncio
async def test_get_reminders(mock_client):
    from apple_reminders.mcp.server import get_reminders
    mock_client.show = AsyncMock(return_value=[Reminder.model_validate(REMINDER_JSON)])
    result = await get_reminders("today")
    mock_client.show.assert_called_once_with("today")
    assert len(result) == 1


@pytest.mark.asyncio
async def test_add_reminder(mock_client):
    from apple_reminders.mcp.server import add_reminder
    mock_client.add = AsyncMock(return_value=Reminder.model_validate(REMINDER_JSON))
    result = await add_reminder("Test")
    mock_client.add.assert_called_once_with("Test", list=None, due=None, notes=None, priority=None)


@pytest.mark.asyncio
async def test_create_list(mock_client):
    from apple_reminders.mcp.server import create_list
    mock_client.create_list = AsyncMock(return_value=ReminderList.model_validate(LIST_JSON))
    result = await create_list("New")
    mock_client.create_list.assert_called_once_with("New")


@pytest.mark.asyncio
async def test_uncomplete_reminder(mock_client):
    from apple_reminders.mcp.server import uncomplete_reminder
    mock_client.uncomplete = AsyncMock(return_value=Reminder.model_validate(REMINDER_JSON))
    result = await uncomplete_reminder("abc123")
    mock_client.uncomplete.assert_called_once_with("abc123")


@pytest.mark.asyncio
async def test_delete_reminder(mock_client):
    from apple_reminders.mcp.server import delete_reminder
    mock_client.delete = AsyncMock(return_value={"deleted": True})
    result = await delete_reminder("abc123")
    mock_client.delete.assert_called_once_with("abc123")


@pytest.mark.asyncio
async def test_check_status(mock_client):
    from apple_reminders.mcp.server import check_status
    mock_client.status = AsyncMock(return_value=AuthStatus.model_validate(STATUS_JSON))
    result = await check_status()
    mock_client.status.assert_called_once()
