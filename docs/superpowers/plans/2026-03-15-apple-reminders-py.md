# apple-reminders-py Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restructure the remindctl-mcp package into apple-reminders-py with a typed async SDK, FastAPI REST server, and MCP server.

**Architecture:** Three layers — models/exceptions at the bottom, async runner + client in the middle, thin MCP and FastAPI servers on top. The runner is the only module aware of the CLI binary.

**Tech Stack:** Python 3.11+, pydantic v2, asyncio, FastAPI, uvicorn, FastMCP

**Spec:** `docs/superpowers/specs/2026-03-15-apple-reminders-py-design.md`

---

## Chunk 1: Foundation (models, exceptions, runner)

### Task 1: Scaffold package and update pyproject.toml

**Files:**
- Delete: `src/remindctl_mcp/` (entire directory)
- Create: `src/apple_reminders/__init__.py`
- Create: `src/apple_reminders/exceptions.py`
- Create: `src/apple_reminders/models.py`
- Create: `src/apple_reminders/runner.py`
- Create: `src/apple_reminders/mcp/__init__.py`
- Create: `src/apple_reminders/api/__init__.py`
- Modify: `pyproject.toml`

- [ ] **Step 1: Delete old package**

```bash
rm -rf src/remindctl_mcp
```

- [ ] **Step 2: Create package directories**

```bash
mkdir -p src/apple_reminders/mcp src/apple_reminders/api
```

- [ ] **Step 3: Create `src/apple_reminders/exceptions.py`**

```python
class RemindersError(Exception):
    """Base exception for apple-reminders operations."""


class RemindersNotFoundError(RemindersError):
    """Raised when the remindctl binary is not found."""


class RemindersTimeoutError(RemindersError):
    """Raised when a remindctl command times out."""


class RemindersAuthError(RemindersError):
    """Raised when remindctl lacks Reminders authorization."""
```

- [ ] **Step 4: Create `src/apple_reminders/models.py`**

```python
from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

Priority = Literal["none", "low", "medium", "high"]
ReminderFilter = Literal[
    "today", "tomorrow", "week", "overdue", "upcoming", "completed", "all"
]


class _Base(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class Reminder(_Base):
    id: str
    title: str
    due_date: datetime | None = None
    is_completed: bool = False
    list_id: str = Field(alias="listID")
    list_name: str
    priority: Priority = "none"
    notes: str | None = None


class ReminderList(_Base):
    id: str
    title: str
    reminder_count: int = 0
    overdue_count: int = 0


class AuthStatus(_Base):
    authorized: bool
    status: str
```

- [ ] **Step 5: Create `src/apple_reminders/runner.py`**

```python
from __future__ import annotations

import asyncio
import json
import shutil

from apple_reminders.exceptions import (
    RemindersError,
    RemindersNotFoundError,
    RemindersTimeoutError,
)

_TIMEOUT_SECONDS = 10


async def run_remindctl(args: list[str]) -> dict | list:
    """Run remindctl asynchronously with --json flag, return parsed JSON."""
    binary = shutil.which("remindctl")
    if binary is None:
        raise RemindersNotFoundError(
            "remindctl not found. Install from https://github.com/steipete/remindctl"
        )

    cmd = [binary, *args, "--json"]

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(
            proc.communicate(), timeout=_TIMEOUT_SECONDS
        )
    except asyncio.TimeoutError:
        proc.kill()
        await proc.communicate()
        raise RemindersTimeoutError(
            f"remindctl timed out after {_TIMEOUT_SECONDS} seconds"
        )

    if proc.returncode != 0:
        raise RemindersError(stderr.decode().strip())

    try:
        return json.loads(stdout.decode())
    except json.JSONDecodeError as e:
        raise RemindersError(f"remindctl returned invalid JSON: {e}")
```

- [ ] **Step 6: Create empty `__init__.py` files**

`src/apple_reminders/__init__.py`:
```python
from apple_reminders.client import AsyncRemindersClient, RemindersClient
from apple_reminders.exceptions import (
    RemindersAuthError,
    RemindersError,
    RemindersNotFoundError,
    RemindersTimeoutError,
)
from apple_reminders.models import AuthStatus, Priority, Reminder, ReminderFilter, ReminderList

__all__ = [
    "AsyncRemindersClient",
    "RemindersClient",
    "RemindersError",
    "RemindersNotFoundError",
    "RemindersTimeoutError",
    "RemindersAuthError",
    "Reminder",
    "ReminderList",
    "ReminderFilter",
    "Priority",
    "AuthStatus",
]
```

`src/apple_reminders/mcp/__init__.py`: empty file
`src/apple_reminders/api/__init__.py`: empty file

- [ ] **Step 7: Update `pyproject.toml`**

```toml
[project]
name = "apple-reminders-py"
version = "0.2.0"
description = "Python SDK, MCP server, and REST API for Apple Reminders"
license = "MIT"
requires-python = ">=3.11"
dependencies = ["pydantic>=2.0"]

[project.optional-dependencies]
mcp = ["fastmcp>=2.0.0"]
api = ["fastapi>=0.100", "uvicorn[standard]"]
all = ["apple-reminders-py[mcp,api]"]

[project.scripts]
remindctl-mcp = "apple_reminders.mcp.server:main"
remindctl-api = "apple_reminders.api.server:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/apple_reminders"]

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"

[dependency-groups]
dev = [
    "pytest>=9.0.2",
    "pytest-asyncio>=0.24",
    "httpx>=0.27",
    "ty>=0.0.23",
]
```

- [ ] **Step 8: Commit scaffold**

```bash
git add -A
git commit -m "refactor: scaffold apple-reminders-py package structure

Replaces remindctl-mcp with new apple_reminders package.
Adds pydantic models, typed exceptions, and async runner."
```

### Task 2: Tests for models and runner

**Files:**
- Create: `tests/test_models.py`
- Create: `tests/test_runner.py` (rewrite)

- [ ] **Step 1: Write model tests `tests/test_models.py`**

```python
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
```

- [ ] **Step 2: Run model tests**

```bash
cd /Users/sphinizy/src/github.com/sam-phinizy/claude-reminders-kit
uv run pytest tests/test_models.py -v
```

Expected: all PASS

- [ ] **Step 3: Rewrite runner tests `tests/test_runner.py`**

```python
import json
from unittest.mock import AsyncMock, patch

import pytest

from apple_reminders.exceptions import (
    RemindersError,
    RemindersNotFoundError,
    RemindersTimeoutError,
)
from apple_reminders.runner import run_remindctl


@pytest.fixture
def mock_binary():
    with patch("apple_reminders.runner.shutil.which", return_value="/usr/local/bin/remindctl") as m:
        yield m


def _make_process(stdout: str = "", stderr: str = "", returncode: int = 0):
    proc = AsyncMock()
    proc.communicate.return_value = (stdout.encode(), stderr.encode())
    proc.returncode = returncode
    proc.kill = AsyncMock()
    return proc


@pytest.mark.asyncio
async def test_returns_list(mock_binary):
    payload = [{"id": "1", "title": "Buy milk"}]
    proc = _make_process(stdout=json.dumps(payload))
    with patch("apple_reminders.runner.asyncio.create_subprocess_exec", return_value=proc):
        result = await run_remindctl(["list"])
    assert result == payload


@pytest.mark.asyncio
async def test_returns_dict(mock_binary):
    payload = {"id": "42", "title": "Take out trash"}
    proc = _make_process(stdout=json.dumps(payload))
    with patch("apple_reminders.runner.asyncio.create_subprocess_exec", return_value=proc):
        result = await run_remindctl(["get", "42"])
    assert result == payload


@pytest.mark.asyncio
async def test_raises_when_binary_not_found():
    with patch("apple_reminders.runner.shutil.which", return_value=None):
        with pytest.raises(RemindersNotFoundError, match="not found"):
            await run_remindctl(["list"])


@pytest.mark.asyncio
async def test_raises_on_nonzero_exit(mock_binary):
    proc = _make_process(stderr="Permission denied", returncode=1)
    with patch("apple_reminders.runner.asyncio.create_subprocess_exec", return_value=proc):
        with pytest.raises(RemindersError, match="Permission denied"):
            await run_remindctl(["list"])


@pytest.mark.asyncio
async def test_raises_on_timeout(mock_binary):
    import asyncio as aio

    proc = _make_process()
    proc.communicate.side_effect = aio.TimeoutError()

    with patch("apple_reminders.runner.asyncio.create_subprocess_exec", return_value=proc):
        with patch("apple_reminders.runner.asyncio.wait_for", side_effect=aio.TimeoutError()):
            with pytest.raises(RemindersTimeoutError, match="timed out"):
                await run_remindctl(["list"])


@pytest.mark.asyncio
async def test_appends_json_flag(mock_binary):
    payload = []
    proc = _make_process(stdout=json.dumps(payload))
    captured = {}

    async def fake_exec(*args, **kwargs):
        captured["cmd"] = args
        return proc

    with patch("apple_reminders.runner.asyncio.create_subprocess_exec", side_effect=fake_exec):
        await run_remindctl(["list", "--filter", "today"])

    assert captured["cmd"][-1] == "--json"


@pytest.mark.asyncio
async def test_raises_on_invalid_json(mock_binary):
    proc = _make_process(stdout="not valid json")
    with patch("apple_reminders.runner.asyncio.create_subprocess_exec", return_value=proc):
        with pytest.raises(RemindersError, match="invalid JSON"):
            await run_remindctl(["list"])
```

- [ ] **Step 4: Run runner tests**

```bash
uv run pytest tests/test_runner.py -v
```

Expected: all PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_models.py tests/test_runner.py
git commit -m "test: add model and async runner tests"
```

## Chunk 2: Client (async + sync)

### Task 3: AsyncRemindersClient

**Files:**
- Create: `src/apple_reminders/client.py`
- Create: `tests/test_client.py`

- [ ] **Step 1: Write client tests `tests/test_client.py`**

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/test_client.py -v
```

Expected: FAIL (client.py doesn't exist yet)

- [ ] **Step 3: Write `src/apple_reminders/client.py`**

```python
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
```

- [ ] **Step 4: Run client tests**

```bash
uv run pytest tests/test_client.py -v
```

Expected: all PASS

- [ ] **Step 5: Commit**

```bash
git add src/apple_reminders/client.py tests/test_client.py
git commit -m "feat: add AsyncRemindersClient and sync wrapper"
```

## Chunk 3: MCP Server

### Task 4: MCP server

**Files:**
- Create: `src/apple_reminders/mcp/server.py`
- Copy: `src/remindctl_mcp/install.py` → `src/apple_reminders/install.py`
- Create: `tests/test_mcp.py`

- [ ] **Step 1: Copy install.py**

Copy the existing `install.py` to `src/apple_reminders/install.py`. Update the `_mcp_entry` function to reference `apple-reminders-py[mcp]` instead of `remindctl-mcp`:

```python
def _mcp_entry() -> dict:
    return {"command": _uvx_path(), "args": ["--refresh", "apple-reminders-py[mcp]"]}
```

- [ ] **Step 2: Write MCP tests `tests/test_mcp.py`**

```python
from unittest.mock import AsyncMock, patch

import pytest

from apple_reminders.models import Reminder, ReminderList, AuthStatus


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
```

- [ ] **Step 3: Write `src/apple_reminders/mcp/server.py`**

```python
from __future__ import annotations

from typing import Literal

from fastmcp import FastMCP

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

mcp = FastMCP("remindctl", instructions=INSTRUCTIONS)
client = AsyncRemindersClient()


@mcp.tool()
async def get_reminders(filter: ReminderFilter | str) -> list[Reminder]:
    """Get reminders by filter.

    Args:
        filter: One of today/tomorrow/week/overdue/upcoming/completed/all or a YYYY-MM-DD date.
    """
    return await client.show(filter)


@mcp.tool()
async def get_lists() -> list[ReminderList]:
    """Get all reminder lists."""
    return await client.lists()


@mcp.tool()
async def get_list(name: str) -> list[Reminder]:
    """Get reminders in a named list."""
    return await client.get_list(name)


@mcp.tool()
async def create_list(name: str) -> ReminderList:
    """Create a new reminder list."""
    return await client.create_list(name)


@mcp.tool()
async def rename_list(name: str, new_name: str) -> ReminderList:
    """Rename a reminder list."""
    return await client.rename_list(name, new_name)


@mcp.tool()
async def delete_list(name: str) -> dict:
    """Delete a reminder list."""
    return await client.delete_list(name, force=True)


@mcp.tool()
async def add_reminder(
    title: str,
    reminder_list: str | None = None,
    due: str | None = None,
    notes: str | None = None,
    priority: Priority | None = None,
) -> Reminder:
    """Add a new reminder."""
    return await client.add(title, list=reminder_list, due=due, notes=notes, priority=priority)


@mcp.tool()
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


@mcp.tool()
async def complete_reminder(ids: list[str]) -> list[Reminder]:
    """Mark one or more reminders as complete."""
    return await client.complete(ids)


@mcp.tool()
async def uncomplete_reminder(id: str) -> Reminder:
    """Mark a reminder as incomplete."""
    return await client.uncomplete(id)


@mcp.tool()
async def delete_reminder(id: str) -> dict:
    """Delete a reminder by ID."""
    return await client.delete(id)


@mcp.tool()
async def check_status() -> AuthStatus:
    """Check the status of the remindctl integration."""
    return await client.status()


def main() -> None:
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "install":
        from apple_reminders.install import run_installer
        run_installer(force="--force" in sys.argv)
    else:
        mcp.run()
```

- [ ] **Step 4: Run MCP tests**

```bash
uv run pytest tests/test_mcp.py -v
```

Expected: all PASS

- [ ] **Step 5: Commit**

```bash
git add src/apple_reminders/mcp/ src/apple_reminders/install.py tests/test_mcp.py
git commit -m "feat: add MCP server with list CRUD and uncomplete tools"
```

## Chunk 4: FastAPI Server

### Task 5: FastAPI server

**Files:**
- Create: `src/apple_reminders/api/server.py`
- Create: `tests/test_api.py`

- [ ] **Step 1: Write API tests `tests/test_api.py`**

```python
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
    from apple_reminders.api.server import app
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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/test_api.py -v
```

Expected: FAIL

- [ ] **Step 3: Write `src/apple_reminders/api/server.py`**

```python
from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from apple_reminders.client import AsyncRemindersClient
from apple_reminders.exceptions import (
    RemindersAuthError,
    RemindersError,
    RemindersNotFoundError,
    RemindersTimeoutError,
)
from apple_reminders.models import Priority

app = FastAPI(title="Apple Reminders API", version="0.2.0")
client = AsyncRemindersClient()


# -- Exception handlers --

@app.exception_handler(RemindersNotFoundError)
async def not_found_handler(request: Request, exc: RemindersNotFoundError):
    return JSONResponse(status_code=404, content={"error": str(exc)})


@app.exception_handler(RemindersAuthError)
async def auth_handler(request: Request, exc: RemindersAuthError):
    return JSONResponse(status_code=403, content={"error": str(exc)})


@app.exception_handler(RemindersTimeoutError)
async def timeout_handler(request: Request, exc: RemindersTimeoutError):
    return JSONResponse(status_code=504, content={"error": str(exc)})


@app.exception_handler(RemindersError)
async def base_handler(request: Request, exc: RemindersError):
    return JSONResponse(status_code=500, content={"error": str(exc)})


# -- Request bodies --

class AddReminderRequest(BaseModel):
    title: str
    list: str | None = None
    due: str | None = None
    notes: str | None = None
    priority: Priority | None = None


class EditReminderRequest(BaseModel):
    title: str | None = None
    due: str | None = None
    notes: str | None = None
    priority: Priority | None = None
    list: str | None = None
    clear_due: bool = False


class CompleteRequest(BaseModel):
    ids: list[str]


class CreateListRequest(BaseModel):
    name: str


class RenameListRequest(BaseModel):
    new_name: str


# -- Reminder routes --

@app.get("/reminders")
async def get_reminders(filter: str = "today", list: str | None = None):
    results = await client.show(filter, list=list)
    return [r.model_dump(by_alias=True) for r in results]


@app.post("/reminders", status_code=201)
async def add_reminder(body: AddReminderRequest):
    result = await client.add(
        body.title, list=body.list, due=body.due, notes=body.notes, priority=body.priority
    )
    return result.model_dump(by_alias=True)


@app.patch("/reminders/{id}")
async def edit_reminder(id: str, body: EditReminderRequest):
    result = await client.edit(
        id, title=body.title, due=body.due, notes=body.notes,
        priority=body.priority, list=body.list, clear_due=body.clear_due,
    )
    return result.model_dump(by_alias=True)


@app.delete("/reminders/{id}")
async def delete_reminder(id: str, force: bool = True):
    return await client.delete(id, force=force)


@app.post("/reminders/complete")
async def complete_reminders(body: CompleteRequest):
    results = await client.complete(body.ids)
    return [r.model_dump(by_alias=True) for r in results]


@app.post("/reminders/{id}/uncomplete")
async def uncomplete_reminder(id: str):
    result = await client.uncomplete(id)
    return result.model_dump(by_alias=True)


# -- List routes --

@app.get("/lists")
async def get_lists():
    results = await client.lists()
    return [rl.model_dump(by_alias=True) for rl in results]


@app.get("/lists/{name}")
async def get_list(name: str):
    results = await client.get_list(name)
    return [r.model_dump(by_alias=True) for r in results]


@app.post("/lists", status_code=201)
async def create_list(body: CreateListRequest):
    result = await client.create_list(body.name)
    return result.model_dump(by_alias=True)


@app.patch("/lists/{name}")
async def rename_list(name: str, body: RenameListRequest):
    result = await client.rename_list(name, body.new_name)
    return result.model_dump(by_alias=True)


@app.delete("/lists/{name}")
async def delete_list(name: str, force: bool = False):
    return await client.delete_list(name, force=force)


# -- Status --

@app.get("/status")
async def get_status():
    result = await client.status()
    return result.model_dump(by_alias=True)


def main() -> None:
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

- [ ] **Step 4: Run API tests**

```bash
uv run pytest tests/test_api.py -v
```

Expected: all PASS

- [ ] **Step 5: Commit**

```bash
git add src/apple_reminders/api/ tests/test_api.py
git commit -m "feat: add FastAPI REST server for Apple Reminders"
```

## Chunk 5: Finalize

### Task 6: Update plugin config and cleanup

**Files:**
- Modify: `.mcp.json`
- Modify: `plugin/.mcp.json`
- Modify: `plugin/.claude-plugin/plugin.json`
- Delete: `tests/test_tools.py`
- Delete: `tests/test_integration.py`

- [ ] **Step 1: Update `.mcp.json`**

```json
{
  "mcpServers": {
    "remindctl": {
      "command": "uvx",
      "args": ["apple-reminders-py[mcp]"]
    }
  }
}
```

- [ ] **Step 2: Update `plugin/.mcp.json`**

```json
{
  "remindctl": {
    "command": "uvx",
    "args": ["--refresh", "apple-reminders-py[mcp]"]
  }
}
```

- [ ] **Step 3: Update `plugin/.claude-plugin/plugin.json`**

Update description to reference the new package name.

- [ ] **Step 4: Delete old test files**

```bash
rm tests/test_tools.py tests/test_integration.py
```

- [ ] **Step 5: Run full test suite**

```bash
uv run pytest -v
```

Expected: all tests pass across test_models, test_runner, test_client, test_mcp, test_api

- [ ] **Step 6: Commit**

```bash
git add -A
git commit -m "chore: update plugin config and clean up old tests"
```
