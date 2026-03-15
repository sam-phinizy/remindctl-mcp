# apple-reminders-py

Python SDK, MCP server, and REST API for Apple Reminders, wrapping the [remindctl](https://github.com/steipete/remindctl) CLI.

## Prerequisites

- macOS 14+
- [remindctl](https://github.com/steipete/remindctl) installed via Homebrew:
  ```bash
  brew install steipete/tap/remindctl
  remindctl authorize
  ```

## Installation

```bash
# SDK only
pip install apple-reminders-py

# SDK + MCP server
pip install apple-reminders-py[mcp]

# SDK + REST API
pip install apple-reminders-py[api]

# Everything
pip install apple-reminders-py[all]
```

## SDK Usage

### Async

```python
from apple_reminders import AsyncRemindersClient

async def main():
    async with AsyncRemindersClient() as client:
        lists = await client.get_lists()
        reminders = await client.get_reminders("today")
        await client.add_reminder("Buy milk", list="Groceries", due="2026-03-16")
```

### Sync

```python
from apple_reminders import RemindersClient

client = RemindersClient()
lists = client.get_lists()
reminders = client.get_reminders("today")
client.add_reminder("Buy milk", list="Groceries", due="2026-03-16")
```

## MCP Server

Run the MCP server directly:

```bash
remindctl-mcp
```

Install into Claude (interactive, configures Claude Code / Claude Desktop / ChatGPT):

```bash
remindctl-mcp install
```

### Manual configuration

#### Claude Code

Add to `.mcp.json` in project root or `~/.claude.json` (user-level):

```json
{
  "mcpServers": {
    "remindctl": {
      "command": "uvx",
      "args": ["--refresh", "apple-reminders-py[mcp]"]
    }
  }
}
```

#### Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "remindctl": {
      "command": "uvx",
      "args": ["--refresh", "apple-reminders-py[mcp]"]
    }
  }
}
```

### Available MCP Tools

- `get_reminders(filter)` — query by today/tomorrow/week/overdue/upcoming/completed/all/YYYY-MM-DD
- `get_lists()` — list all reminder lists
- `get_list(name)` — reminders in a specific list
- `add_reminder(title, list?, due?, notes?, priority?)` — create a reminder
- `edit_reminder(id, title?, due?, notes?, priority?, list?, clear_due?)` — update a reminder
- `complete_reminder(ids)` — mark complete
- `delete_reminder(id)` — delete a reminder
- `check_status()` — verify permission status

## FastAPI Server

Run the REST API server:

```bash
remindctl-api
```

Routes:

- `GET /reminders` — list reminders (query param: `filter`)
- `GET /lists` — all reminder lists
- `GET /lists/{name}` — reminders in a specific list
- `POST /reminders` — create a reminder
- `PATCH /reminders/{id}` — update a reminder
- `POST /reminders/{id}/complete` — mark complete
- `DELETE /reminders/{id}` — delete a reminder
- `GET /status` — check remindctl permission status

## Claude Code Plugin

The `plugin/` directory contains a Claude Code plugin with the **text-to-reminders** skill, which parses emails, Slack threads, and meeting notes into structured reminders automatically.

```bash
claude plugin add sam-phinizy/claude-reminders-kit --path plugin
```

See [`plugin/README.md`](plugin/README.md) for details.

## Development

```bash
git clone https://github.com/sam-phinizy/claude-reminders-kit
cd claude-reminders-kit
uv sync
uv run pytest
```

## License

MIT
