from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from apple_reminders.models import AuthStatus, Priority, Reminder, ReminderList
from apple_reminders.runner import run_remindctl

if TYPE_CHECKING:
    from apple_reminders.models import ReminderFilter


class AsyncRemindersClient:
    """Async client for Apple Reminders via remindctl."""

    async def show(
        self,
        filter: ReminderFilter | str = "today",
        *,
        list: str | None = None,
    ) -> list[Reminder]:
        args = ["show", filter]
        if list is not None:
            args += ["--list", list]
        data = await run_remindctl(args)
        return [Reminder.model_validate(r) for r in data]

    async def add(
        self,
        title: str,
        *,
        list: str | None = None,
        due: str | None = None,
        notes: str | None = None,
        priority: Priority | None = None,
    ) -> Reminder:
        args = ["add", "--title", title]
        if list is not None:
            args += ["--list", list]
        if due is not None:
            args += ["--due", due]
        if notes is not None:
            args += ["--notes", notes]
        if priority is not None:
            args += ["--priority", priority]
        data = await run_remindctl(args)
        return Reminder.model_validate(data)

    async def edit(
        self,
        id: str,
        *,
        title: str | None = None,
        due: str | None = None,
        notes: str | None = None,
        priority: Priority | None = None,
        list: str | None = None,
        clear_due: bool = False,
    ) -> Reminder:
        if not any([title, due, notes, priority, list, clear_due]):
            raise ValueError("At least one field must be provided to edit")
        args = ["edit", id]
        if title is not None:
            args += ["--title", title]
        if due is not None:
            args += ["--due", due]
        if notes is not None:
            args += ["--notes", notes]
        if priority is not None:
            args += ["--priority", priority]
        if list is not None:
            args += ["--list", list]
        if clear_due:
            args += ["--clear-due"]
        data = await run_remindctl(args)
        return Reminder.model_validate(data)

    async def complete(self, ids: list[str]) -> list[Reminder]:
        data = await run_remindctl(["complete", *ids])
        if isinstance(data, dict):
            return [Reminder.model_validate(data)]
        return [Reminder.model_validate(r) for r in data]

    async def uncomplete(self, id: str) -> Reminder:
        data = await run_remindctl(["edit", id, "--incomplete"])
        return Reminder.model_validate(data)

    async def delete(self, id: str, *, force: bool = True) -> dict:
        args = ["delete", id]
        if force:
            args += ["--force"]
        data = await run_remindctl(args)
        return data if isinstance(data, dict) else {}

    async def lists(self) -> list[ReminderList]:
        data = await run_remindctl(["list"])
        return [ReminderList.model_validate(rl) for rl in data]

    async def get_list(self, name: str) -> list[Reminder]:
        data = await run_remindctl(["list", name])
        return [Reminder.model_validate(r) for r in data]

    async def create_list(self, name: str) -> ReminderList:
        data = await run_remindctl(["list", name, "--create"])
        return ReminderList.model_validate(data)

    async def rename_list(self, name: str, new_name: str) -> ReminderList:
        data = await run_remindctl(["list", name, "--rename", new_name])
        return ReminderList.model_validate(data)

    async def delete_list(self, name: str, *, force: bool = False) -> dict:
        args = ["list", name, "--delete"]
        if force:
            args += ["--force"]
        data = await run_remindctl(args)
        return data if isinstance(data, dict) else {}

    async def status(self) -> AuthStatus:
        data = await run_remindctl(["status"])
        return AuthStatus.model_validate(data)


class RemindersClient:
    """Sync wrapper around AsyncRemindersClient.

    Intended for scripts and REPL use. Do not use inside an async context.
    """

    def __init__(self) -> None:
        self._async = AsyncRemindersClient()

    def show(self, filter="today", *, list=None):
        return asyncio.run(self._async.show(filter, list=list))

    def add(self, title, *, list=None, due=None, notes=None, priority=None):
        return asyncio.run(self._async.add(title, list=list, due=due, notes=notes, priority=priority))

    def edit(self, id, *, title=None, due=None, notes=None, priority=None, list=None, clear_due=False):
        return asyncio.run(self._async.edit(id, title=title, due=due, notes=notes, priority=priority, list=list, clear_due=clear_due))

    def complete(self, ids):
        return asyncio.run(self._async.complete(ids))

    def uncomplete(self, id):
        return asyncio.run(self._async.uncomplete(id))

    def delete(self, id, *, force=True):
        return asyncio.run(self._async.delete(id, force=force))

    def lists(self):
        return asyncio.run(self._async.lists())

    def get_list(self, name):
        return asyncio.run(self._async.get_list(name))

    def create_list(self, name):
        return asyncio.run(self._async.create_list(name))

    def rename_list(self, name, new_name):
        return asyncio.run(self._async.rename_list(name, new_name))

    def delete_list(self, name, *, force=False):
        return asyncio.run(self._async.delete_list(name, force=force))

    def status(self):
        return asyncio.run(self._async.status())
