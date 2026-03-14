# remindctl MCP Server — Design Spec

**Date:** 2026-03-14
**Status:** Approved

## Overview

A Python MCP server (`remindctl-mcp`) that wraps the [`remindctl`](https://github.com/steipete/remindctl) CLI, exposing Apple Reminders management as MCP tools usable in both Claude Code and Claude.ai desktop (Cowork).

## Goals

- Full CRUD access to Apple Reminders from Claude
- Works in Claude Code and Claude.ai desktop (Cowork) via MCP
- Distributable via `uvx` — no install step required
- Guides Claude to behave safely and helpfully through server-level instructions

## Non-Goals

- Direct macOS EventKit/PyObjC integration (remindctl handles this)
- GUI or web interface
- Support for non-macOS platforms

## Architecture

### Package Structure

```
remindctl-mcp/
├── pyproject.toml              # uvx entry point defined in [project.scripts]
├── src/
│   └── remindctl_mcp/
│       ├── __init__.py
│       ├── server.py           # FastMCP app + all @mcp.tool() definitions
│       └── runner.py           # subprocess wrapper: run_remindctl(args) -> dict | list
```

`pyproject.toml` must define:
```toml
[project.scripts]
remindctl-mcp = "remindctl_mcp.server:main"
```

Where `main()` calls `mcp.run()` on the FastMCP instance.

### Data Flow

1. Claude calls an MCP tool (e.g. `add_reminder`)
2. `server.py` maps parameters to `remindctl` CLI args
3. `runner.py` executes `remindctl ... --json`, captures stdout
4. JSON is parsed and returned as structured content to Claude

`runner.py` contract: returns a `list` for collection queries (e.g. `get_reminders`, `get_lists`), a `dict` for single-item operations (e.g. `add_reminder`). Raises a `RemindctlError` on non-zero exit, binary not found, or timeout. Callers in `server.py` do not need to type-narrow — each tool calls the appropriate command and expects the correct shape.

### Distribution

Installed and run via `uvx remindctl-mcp`. MCP config in both Claude Code and Claude desktop points to `uvx remindctl-mcp`. To update to a newer version: `uvx --no-cache remindctl-mcp`.

**Versioning:** Package follows semver starting at `0.1.0`. A breaking change is defined as removing a tool, renaming a tool, or removing a parameter. Patch versions fix bugs; minor versions add tools or parameters. Breaking `remindctl` CLI changes are handled by bumping the major version.

## MCP Tools

### Date/Time Formats

**For `due` parameters** (`add_reminder`, `edit_reminder`): accepts `today`, `tomorrow`, `yesterday`, `YYYY-MM-DD`, `YYYY-MM-DD HH:mm`, or ISO 8601 — matching what `remindctl --due` accepts. The MCP layer does not validate this; invalid values surface as CLI errors.

**For `get_reminders` filter**: accepts only `today`, `tomorrow`, `week`, `overdue`, `upcoming`, `completed`, `all`, or `YYYY-MM-DD`. `yesterday` is not a valid filter value.

### Query Tools

| Tool | Parameters | remindctl command | Notes |
|------|-----------|-------------------|-------|
| `get_reminders` | `filter: str` (required) | `remindctl <filter> --json` | No default. Must be one of: `today`, `tomorrow`, `week`, `overdue`, `upcoming`, `completed`, `all`, `YYYY-MM-DD`. |
| `get_lists` | none | `remindctl list --json` | Returns all reminder lists |
| `get_list` | `name: str` | `remindctl list <name> --json` | Returns all reminders in the named list |

### Mutation Tools

| Tool | Parameters | remindctl command | Notes |
|------|-----------|-------------------|-------|
| `add_reminder` | `title: str`, `list: str \| None`, `due: str \| None` | `remindctl add --title "..." [--list <name>] [--due <date>] --json` | `list` is a list name string matching output from `get_lists`. When `list` is omitted, `remindctl` adds to the default "Reminders" list. Server instructions prompt Claude to confirm this with the user. |
| `edit_reminder` | `id: str`, `title: str \| None`, `due: str \| None` | `remindctl edit <id> [--title ...] [--due ...] --json` | At least one of `title` or `due` must be provided; tool raises error if both are None. Moving a reminder to a different list is not supported by `remindctl edit`. |
| `complete_reminder` | `ids: list[str]` | `remindctl complete <id1> <id2> ... --json` | Confirmation is required regardless of how many IDs are provided. On non-zero exit, the entire operation is reported as failed with CLI stderr — no rollback. |
| `delete_reminder` | `id: str` | `remindctl delete <id> --force --json` | `--force` is intentional; Claude-level confirmation is the gate. |

### System Tools

| Tool | Parameters | remindctl command | Notes |
|------|-----------|-------------------|-------|
| `check_status` | none | `remindctl status --json` | Returns permission status |

**Note on `authorize`:** `remindctl authorize` triggers a macOS system permissions dialog requiring direct terminal interaction. It cannot be meaningfully invoked via MCP. If permission is missing, instruct the user to run `remindctl authorize` in a terminal.

## Server Instructions

Server-level behavioral guidance is provided via the `instructions=` parameter of the `FastMCP(...)` constructor. This string is surfaced to Claude as system-level context. It guides Claude's reasoning — it is not enforced at the code level.

### Safety Instructions

- Before `delete_reminder`, show the reminder title/details and ask the user to confirm
- Before `complete_reminder` (any number of IDs), list what will be marked complete and confirm
- Before `add_reminder`: if `list` is specified, proceed. If `list` is not specified, inform the user that remindctl will add to the default "Reminders" list, and ask if they want to choose a different list (call `get_lists` if they do)
- If `remindctl` is not found or lacks permission, surface a clear message and instruct the user to run `remindctl authorize` in a terminal

### Workflow Instructions

- After adding a reminder, confirm it was created and echo back the due date if set
- After completing or deleting, offer a relevant follow-up (e.g. "Want to see today's remaining reminders?")
- When querying, proactively note if there are overdue items alongside the requested view

## Error Handling

| Scenario | Handling |
|----------|----------|
| `remindctl` binary not found | Raise tool error: "remindctl not found. Install from https://github.com/steipete/remindctl" |
| Non-zero exit code | Raise FastMCP tool error with stderr content |
| Permission denied | Detect via `check_status()`, instruct user to run `remindctl authorize` in a terminal |
| Subprocess timeout | All calls use 10s timeout; raise tool error on timeout |
| `edit_reminder` with no fields | Raise tool error before invoking CLI: "At least one of title or due must be provided" |

## Testing

- **Unit tests:** Mock `runner.py` subprocess layer — test each tool's arg construction and JSON parsing independently. All mutation tools have unit tests.
- **Integration tests:** Call the real `remindctl` binary; skipped if not on PATH (`shutil.which`). Integration tests are read-only by default (query tools only). Mutation integration tests (add/edit/complete/delete) are opt-in via `REMINDCTL_TEST_LIST` env var — they run against a dedicated list named by that variable, never against the user's real data.
- **Run tests:** `uv run pytest`

## Dependencies

- Python 3.11+
- `fastmcp`
- `remindctl` binary installed on macOS 14+ (external, not a Python dep)

## MCP Configuration

### Claude Code

Claude Code supports MCP configuration at the project level (`.mcp.json` in the project root) or user level (`~/.claude.json`). Add under `mcpServers`:

```json
{
  "mcpServers": {
    "remindctl": {
      "command": "uvx",
      "args": ["remindctl-mcp"]
    }
  }
}
```

### Claude Desktop (`~/Library/Application Support/Claude/claude_desktop_config.json`)

```json
{
  "mcpServers": {
    "remindctl": {
      "command": "uvx",
      "args": ["remindctl-mcp"]
    }
  }
}
```

To pin a specific version: `"args": ["remindctl-mcp==1.0.0"]`. To force update: run `uvx --no-cache remindctl-mcp` once.
