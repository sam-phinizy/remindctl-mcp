from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

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
    with patch("apple_reminders.api.server.client") as m:
        yield m


@pytest.fixture
async def http(mock_client):
    from apple_reminders.api.server import create_app
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.mark.asyncio
async def test_get_reminders(http, mock_client):
    mock_client.show = AsyncMock(return_value=[Reminder.model_validate(REMINDER_JSON)])
    resp = await http.get("/reminders", params={"filter": "today"})
    assert resp.status_code == 200
    assert len(resp.json()) == 1
    assert resp.json()[0]["title"] == "Test"


@pytest.mark.asyncio
async def test_get_reminders_with_list(http, mock_client):
    mock_client.show = AsyncMock(return_value=[])
    resp = await http.get("/reminders", params={"filter": "today", "list": "Work"})
    assert resp.status_code == 200
    mock_client.show.assert_called_once_with("today", list="Work")


@pytest.mark.asyncio
async def test_add_reminder(http, mock_client):
    mock_client.add = AsyncMock(return_value=Reminder.model_validate(REMINDER_JSON))
    resp = await http.post("/reminders", json={"title": "Test"})
    assert resp.status_code == 201
    assert resp.json()["title"] == "Test"


@pytest.mark.asyncio
async def test_edit_reminder(http, mock_client):
    mock_client.edit = AsyncMock(return_value=Reminder.model_validate(REMINDER_JSON))
    resp = await http.patch("/reminders/abc123", json={"title": "New"})
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_delete_reminder(http, mock_client):
    mock_client.delete = AsyncMock(return_value={"deleted": True})
    resp = await http.delete("/reminders/abc123")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_complete_reminders(http, mock_client):
    mock_client.complete = AsyncMock(return_value=[Reminder.model_validate(REMINDER_JSON)])
    resp = await http.post("/reminders/complete", json={"ids": ["abc123"]})
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_uncomplete_reminder(http, mock_client):
    mock_client.uncomplete = AsyncMock(return_value=Reminder.model_validate(REMINDER_JSON))
    resp = await http.post("/reminders/abc123/uncomplete")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_get_lists(http, mock_client):
    mock_client.lists = AsyncMock(return_value=[ReminderList.model_validate(LIST_JSON)])
    resp = await http.get("/lists")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


@pytest.mark.asyncio
async def test_get_list(http, mock_client):
    mock_client.get_list = AsyncMock(return_value=[Reminder.model_validate(REMINDER_JSON)])
    resp = await http.get("/lists/Reminders")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_create_list(http, mock_client):
    mock_client.create_list = AsyncMock(return_value=ReminderList.model_validate(LIST_JSON))
    resp = await http.post("/lists", json={"name": "New"})
    assert resp.status_code == 201


@pytest.mark.asyncio
async def test_rename_list(http, mock_client):
    mock_client.rename_list = AsyncMock(return_value=ReminderList.model_validate(LIST_JSON))
    resp = await http.patch("/lists/Old", json={"new_name": "New"})
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_delete_list(http, mock_client):
    mock_client.delete_list = AsyncMock(return_value={"deleted": True})
    resp = await http.delete("/lists/Old", params={"force": "true"})
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_status(http, mock_client):
    mock_client.status = AsyncMock(return_value=AuthStatus.model_validate(STATUS_JSON))
    resp = await http.get("/status")
    assert resp.status_code == 200
    assert resp.json()["authorized"] is True
