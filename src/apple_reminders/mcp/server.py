from __future__ import annotations

from typing import Literal

from apple_reminders.client import AsyncRemindersClient
from apple_reminders.models import (
    AuthStatus,
    Priority,
    Reminder,
    ReminderList,
)

ReminderFilter = Literal[
    "today", "tomorrow", "week", "overdue", "upcoming", "completed", "all"
]

INSTRUCTIONS = """You are managing Apple Reminders via remindctl.

Safety rules:
- Before delete_reminder, show the reminder title/details and ask the user to confirm.
- Before complete_reminder (any number of IDs), list what will be marked complete and confirm with the user.
- Before add_reminder: if list is specified, proceed. If list is not specified, inform the user that remindctl will add to the default "Reminders" list, and ask if they want to choose a different list (call get_lists if they do).
- If remindctl is not found or lacks permission, surface a clear message and instruct the user to run `remindctl authorize` in a terminal.

Workflow rules:
- After adding a reminder, confirm it was created and echo back the due date if set.
- After completing or deleting, offer a relevant follow-up (e.g. "Want to see today's remaining reminders?").
- When querying, proactively note if there are overdue items alongside the requested view.
"""

client = AsyncRemindersClient()


async def get_reminders(filter: ReminderFilter | str) -> list[Reminder]:
    """Get reminders by filter.

    Args:
        filter: One of today/tomorrow/week/overdue/upcoming/completed/all or a YYYY-MM-DD date.
    """
    return await client.show(filter)


async def get_lists() -> list[ReminderList]:
    """Get all reminder lists."""
    return await client.lists()


async def get_list(name: str) -> list[Reminder]:
    """Get reminders in a named list."""
    return await client.get_list(name)


async def create_list(name: str) -> ReminderList:
    """Create a new reminder list."""
    return await client.create_list(name)


async def rename_list(name: str, new_name: str) -> ReminderList:
    """Rename a reminder list."""
    return await client.rename_list(name, new_name)


async def delete_list(name: str) -> dict:
    """Delete a reminder list."""
    return await client.delete_list(name, force=True)


async def add_reminder(
    title: str,
    reminder_list: str | None = None,
    due: str | None = None,
    notes: str | None = None,
    priority: Priority | None = None,
) -> Reminder:
    """Add a new reminder."""
    return await client.add(title, list=reminder_list, due=due, notes=notes, priority=priority)


async def edit_reminder(
    id: str,
    title: str | None = None,
    due: str | None = None,
    notes: str | None = None,
    priority: Priority | None = None,
    reminder_list: str | None = None,
    clear_due: bool = False,
) -> Reminder:
    """Edit an existing reminder."""
    return await client.edit(
        id, title=title, due=due, notes=notes, priority=priority, list=reminder_list, clear_due=clear_due
    )


async def complete_reminder(ids: list[str]) -> list[Reminder]:
    """Mark one or more reminders as complete."""
    return await client.complete(ids)


async def uncomplete_reminder(id: str) -> Reminder:
    """Mark a reminder as incomplete."""
    return await client.uncomplete(id)


async def delete_reminder(id: str) -> dict:
    """Delete a reminder by ID."""
    return await client.delete(id)


async def check_status() -> AuthStatus:
    """Check the status of the remindctl integration."""
    return await client.status()


def create_app():
    """Create and return the FastMCP app. Lazily imports fastmcp."""
    from fastmcp import FastMCP  # lazy import — requires apple-reminders-py[mcp]

    mcp = FastMCP("remindctl", instructions=INSTRUCTIONS)

    mcp.tool()(get_reminders)
    mcp.tool()(get_lists)
    mcp.tool()(get_list)
    mcp.tool()(create_list)
    mcp.tool()(rename_list)
    mcp.tool()(delete_list)
    mcp.tool()(add_reminder)
    mcp.tool()(edit_reminder)
    mcp.tool()(complete_reminder)
    mcp.tool()(uncomplete_reminder)
    mcp.tool()(delete_reminder)
    mcp.tool()(check_status)

    return mcp


def main() -> None:
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "install":
        from apple_reminders.install import run_installer
        run_installer(force="--force" in sys.argv)
    else:
        app = create_app()
        app.run()
