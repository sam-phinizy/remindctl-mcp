# apple-reminders-py Design Spec

## Overview

Restructure the existing `remindctl-mcp` package into `apple-reminders-py` — a Python library providing an async/sync SDK for Apple Reminders, plus optional MCP and FastAPI server interfaces. The SDK wraps the `remindctl` CLI today but is designed so the backend can be swapped (e.g., direct EventKit bindings) without changing the public API.

## Package Structure

```
src/apple_reminders/
├── __init__.py          # re-exports client, models, exceptions
├── models.py            # Pydantic models
├── client.py            # AsyncRemindersClient + sync RemindersClient
├── runner.py            # async subprocess execution layer
├── exceptions.py        # RemindersError and subclasses
├── mcp/
│   ├── __init__.py
│   └── server.py        # FastMCP server
├── api/
│   ├── __init__.py
│   └── server.py        # FastAPI app
└── install.py           # existing MCP installer (carried over)
```

## CLI JSON Output Reference

Sample `remindctl` JSON responses used to derive pydantic models.

**Reminder** (`remindctl show today --json`):
```json
{
  "dueDate": "2026-03-15T04:00:00Z",
  "id": "2B8FDA10-EDFB-48EA-9122-33E145F83BC5",
  "isCompleted": false,
  "listID": "F0564D4C-7053-54EB-3B69-54030D5E1F5B",
  "listName": "Reminders",
  "priority": "none",
  "title": "Clean up basement"
}
```

**ReminderList** (`remindctl list --json`):
```json
{
  "id": "F0564D4C-7053-54EB-3B69-54030D5E1F5B",
  "overdueCount": 3,
  "reminderCount": 8,
  "title": "Reminders"
}
```

**AuthStatus** (`remindctl status --json`):
```json
{
  "authorized": true,
  "status": "full-access"
}
```

## Models (`models.py`)

All models use pydantic v2 with `alias_generator=to_camel` and `populate_by_name=True` to accept both camelCase (from CLI) and snake_case (from Python).

```python
from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel
from datetime import datetime
from typing import Literal

Priority = Literal["none", "low", "medium", "high"]
ReminderFilter = Literal["today", "tomorrow", "week", "overdue", "upcoming", "completed", "all"]
# Note: ReminderFilter is used for type hints but the client also accepts
# arbitrary date strings (YYYY-MM-DD) via the `| str` union on method signatures.

class _Base(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

class Reminder(_Base):
    id: str
    title: str
    due_date: datetime | None = None
    is_completed: bool = False
    list_id: str                    # "listID" in CLI JSON
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

Note: The CLI uses `listID` (not `listId`). The `to_camel` generator produces `listId`, so the `list_id` field needs an explicit `Field(alias="listID")` override.

## Runner (`runner.py`)

Async subprocess wrapper using `asyncio.create_subprocess_exec`. Finds `remindctl` binary via `shutil.which`, runs it with `--json`, parses JSON output. Raises typed exceptions on failure.

```python
async def run_remindctl(args: list[str]) -> dict | list:
    """Run remindctl asynchronously with --json flag, return parsed JSON.

    Uses asyncio.create_subprocess_exec for non-blocking execution.
    """
```

This is the only module that knows about the CLI binary. Swapping backends means replacing this module.

## Client (`client.py`)

### AsyncRemindersClient

Primary interface. All methods return typed pydantic models.

**Reminders:**

```python
async def show(filter: ReminderFilter | str = "today", *, list: str | None = None) -> list[Reminder]
async def add(title: str, *, list: str | None = None, due: str | None = None, notes: str | None = None, priority: Priority | None = None) -> Reminder
async def edit(id: str, *, title: str | None = None, due: str | None = None, notes: str | None = None, priority: Priority | None = None, list: str | None = None, clear_due: bool = False) -> Reminder
async def complete(ids: list[str]) -> list[Reminder]
async def uncomplete(id: str) -> Reminder
async def delete(id: str, *, force: bool = True) -> dict
```

**Lists:**

```python
async def lists() -> list[ReminderList]
async def get_list(name: str) -> list[Reminder]
async def create_list(name: str) -> ReminderList
async def rename_list(name: str, new_name: str) -> ReminderList
async def delete_list(name: str, *, force: bool = False) -> dict
```

**Status:**

```python
async def status() -> AuthStatus
```

### RemindersClient (sync wrapper)

Thin sync wrapper. Uses `asyncio.run()` for each method call. Same method signatures, same return types. Note: `asyncio.run()` will raise `RuntimeError` if called from within an existing event loop — this is intentional, as the sync client is meant for scripts and REPL use, not for use inside async contexts.

## FastAPI Server (`api/server.py`)

REST API mirroring the client methods. Each CLI subcommand maps to a route.

`RemindersError` subclasses map to HTTP status codes:
- `RemindersNotFoundError` → 404
- `RemindersAuthError` → 403
- `RemindersTimeoutError` → 504
- `RemindersError` (base) → 500

**Reminders:**

| Method | Route | Client method | Request body / params |
|--------|-------|---------------|----------------------|
| GET | `/reminders` | `show()` | query: `filter`, `list` |
| POST | `/reminders` | `add()` | body: `title`, `list`, `due`, `notes`, `priority` |
| PATCH | `/reminders/{id}` | `edit()` | body: `title`, `due`, `notes`, `priority`, `list`, `clear_due` |
| DELETE | `/reminders/{id}` | `delete()` | query: `force` (default: `true`) |
| POST | `/reminders/complete` | `complete()` | body: `ids` |
| POST | `/reminders/{id}/uncomplete` | `uncomplete()` | - |

**Lists:**

| Method | Route | Client method | Request body / params |
|--------|-------|---------------|----------------------|
| GET | `/lists` | `lists()` | - |
| GET | `/lists/{name}` | `get_list()` | - |
| POST | `/lists` | `create_list()` | body: `name` |
| PATCH | `/lists/{name}` | `rename_list()` | body: `new_name` |
| DELETE | `/lists/{name}` | `delete_list()` | query: `force` (default: `false`) |

**Status:**

| Method | Route | Client method |
|--------|-------|---------------|
| GET | `/status` | `status()` |

Entry point: `remindctl-api` runs uvicorn on `0.0.0.0:8000`.

## MCP Server (`mcp/server.py`)

Carries over all existing tools from current `server.py`, refactored to use `AsyncRemindersClient` instead of calling `run_remindctl` directly. Carries over the existing `INSTRUCTIONS` string for LLM safety/workflow guidance.

**Existing tools** (carried over): `get_reminders`, `get_lists`, `get_list`, `add_reminder`, `edit_reminder`, `complete_reminder`, `delete_reminder`, `check_status`.

**New tools**: `create_list`, `rename_list`, `delete_list`, `uncomplete_reminder`.

Entry point: `remindctl-mcp` (unchanged). The `remindctl-mcp install` subcommand is preserved via the carried-over `install.py` module and the `main()` function's argv dispatch.

## pyproject.toml

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
```

## Migration from remindctl-mcp

- Delete `src/remindctl_mcp/` entirely
- Create `src/apple_reminders/` with new structure
- Update `pyproject.toml` with new name, deps, entry points
- Update plugin config (`.mcp.json`, `plugin/`) to reference new package name
- Update tests

## Error Handling

```python
class RemindersError(Exception): ...
class RemindersNotFoundError(RemindersError): ...  # binary not found
class RemindersTimeoutError(RemindersError): ...   # subprocess timeout
class RemindersAuthError(RemindersError): ...      # not authorized
```

## Testing

- Unit tests mock `runner.run_remindctl` to test client methods with fixture JSON
- Integration tests (opt-in) hit the real CLI
- FastAPI tests use `httpx.AsyncClient` with `TestClient`
