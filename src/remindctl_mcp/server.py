from typing import Literal

from fastmcp import FastMCP
from remindctl_mcp.runner import run_remindctl, RemindctlError

ReminderFilter = Literal["today", "tomorrow", "week", "overdue", "upcoming", "completed", "all"]

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

mcp = FastMCP("remindctl", instructions=INSTRUCTIONS)


@mcp.tool()
def get_reminders(filter: ReminderFilter | str) -> dict | list:
    """Get reminders by filter.

    Args:
        filter: One of today/tomorrow/week/overdue/upcoming/completed/all or a YYYY-MM-DD date.
    """
    return run_remindctl([filter])


@mcp.tool()
def get_lists() -> dict | list:
    """Get all reminder lists."""
    return run_remindctl(["list"])


@mcp.tool()
def get_list(name: str) -> dict | list:
    """Get reminders in a named list.

    Args:
        name: The name of the reminder list to retrieve.
    """
    return run_remindctl(["list", name])


@mcp.tool()
def add_reminder(title: str, reminder_list: str | None = None, due: str | None = None) -> dict | list:
    """Add a new reminder.

    Args:
        title: The title of the reminder.
        reminder_list: Optional list name to add the reminder to (defaults to "Reminders").
        due: Optional due date in YYYY-MM-DD or ISO 8601 format.
    """
    args = ["add", "--title", title]
    if reminder_list is not None:
        args += ["--list", reminder_list]
    if due is not None:
        args += ["--due", due]
    return run_remindctl(args)


@mcp.tool()
def edit_reminder(id: str, title: str | None = None, due: str | None = None) -> dict | list:
    """Edit an existing reminder.

    Args:
        id: The ID of the reminder to edit.
        title: New title for the reminder.
        due: New due date in YYYY-MM-DD or ISO 8601 format.
    """
    if title is None and due is None:
        raise ValueError("At least one of title or due must be provided")
    args = ["edit", id]
    if title is not None:
        args += ["--title", title]
    if due is not None:
        args += ["--due", due]
    return run_remindctl(args)


@mcp.tool()
def complete_reminder(ids: list[str]) -> dict | list:
    """Mark one or more reminders as complete.

    Args:
        ids: List of reminder IDs to mark as complete.
    """
    return run_remindctl(["complete"] + ids)


@mcp.tool()
def delete_reminder(id: str) -> dict | list:
    """Delete a reminder by ID.

    Args:
        id: The ID of the reminder to delete.
    """
    return run_remindctl(["delete", id, "--force"])


@mcp.tool()
def check_status() -> dict | list:
    """Check the status of the remindctl integration."""
    return run_remindctl(["status"])


def main():
    mcp.run()
