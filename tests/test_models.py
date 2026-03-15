from datetime import datetime, timezone

from apple_reminders.models import AuthStatus, Reminder, ReminderList


def test_reminder_from_cli_json():
    data = {
        "dueDate": "2026-03-15T04:00:00Z",
        "id": "2B8FDA10-EDFB-48EA-9122-33E145F83BC5",
        "isCompleted": False,
        "listID": "F0564D4C-7053-54EB-3B69-54030D5E1F5B",
        "listName": "Reminders",
        "priority": "none",
        "title": "Clean up basement",
    }
    r = Reminder.model_validate(data)
    assert r.id == "2B8FDA10-EDFB-48EA-9122-33E145F83BC5"
    assert r.title == "Clean up basement"
    assert r.due_date == datetime(2026, 3, 15, 4, 0, tzinfo=timezone.utc)
    assert r.is_completed is False
    assert r.list_id == "F0564D4C-7053-54EB-3B69-54030D5E1F5B"
    assert r.list_name == "Reminders"
    assert r.priority == "none"
    assert r.notes is None


def test_reminder_from_snake_case():
    r = Reminder(
        id="abc",
        title="Test",
        list_id="list1",
        list_name="Work",
    )
    assert r.id == "abc"
    assert r.list_id == "list1"


def test_reminder_optional_fields():
    data = {
        "id": "abc",
        "title": "No due date",
        "isCompleted": False,
        "listID": "list1",
        "listName": "Reminders",
        "priority": "none",
    }
    r = Reminder.model_validate(data)
    assert r.due_date is None
    assert r.notes is None


def test_reminder_list_from_cli_json():
    data = {
        "id": "F0564D4C-7053-54EB-3B69-54030D5E1F5B",
        "overdueCount": 3,
        "reminderCount": 8,
        "title": "Reminders",
    }
    rl = ReminderList.model_validate(data)
    assert rl.title == "Reminders"
    assert rl.reminder_count == 8
    assert rl.overdue_count == 3


def test_auth_status_from_cli_json():
    data = {"authorized": True, "status": "full-access"}
    s = AuthStatus.model_validate(data)
    assert s.authorized is True
    assert s.status == "full-access"
