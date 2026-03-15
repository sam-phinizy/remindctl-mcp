# remindctl-mcp

MCP server for Apple Reminders via [remindctl](https://github.com/steipete/remindctl). Expose Apple Reminders management to Claude and ChatGPT via the Model Context Protocol.

## Prerequisites

- macOS 14+
- [remindctl](https://github.com/steipete/remindctl) installed
- [uv](https://docs.astral.sh/uv/) installed (for uvx)
- Grant Reminders permission: run `remindctl authorize` once in terminal

## Available Tools

- `get_reminders(filter)` — query by today/tomorrow/week/overdue/upcoming/completed/all/YYYY-MM-DD
- `get_lists()` — list all reminder lists
- `get_list(name)` — reminders in a specific list
- `add_reminder(title, list?, due?, notes?, priority?)` — create a reminder
- `edit_reminder(id, title?, due?, notes?, priority?, list?, clear_due?)` — update a reminder
- `complete_reminder(ids)` — mark complete
- `delete_reminder(id)` — delete a reminder
- `check_status()` — verify permission status

## Installation

### Interactive installer (recommended)

Run the installer and follow the prompts to configure any combination of Claude Code, Claude Desktop, and ChatGPT:

```bash
uvx remindctl-mcp install
```

### Manual configuration

#### Claude Code

Add to `.mcp.json` in project root or `~/.claude.json` (user-level):

```json
{
  "mcpServers": {
    "remindctl": {
      "command": "uvx",
      "args": ["--refresh", "remindctl-mcp"]
    }
  }
}
```

#### Claude Desktop (including Cowork)

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "remindctl": {
      "command": "uvx",
      "args": ["--refresh", "remindctl-mcp"]
    }
  }
}
```

#### ChatGPT Desktop

ChatGPT Desktop supports MCP servers. Add to ChatGPT's MCP config (Settings → Advanced → MCP Servers):

```json
{
  "remindctl": {
    "command": "uvx",
    "args": ["--refresh", "remindctl-mcp"]
  }
}
```

## Updating

```bash
uvx --no-cache remindctl-mcp
```

## Claude Code Plugin

For Claude Code users, there's also a plugin with the **text-to-reminders** skill — it parses emails, Slack threads, and meeting notes into structured reminders automatically.

```bash
claude plugin add sam-phinizy/remindctl-mcp --path plugin
```

Or install via the [sams-claude-menagerie](https://github.com/sam-phinizy/sams-claude-menagerie) marketplace:

```bash
claude plugin add sam-phinizy/sams-claude-menagerie
```

See [`plugin/README.md`](plugin/README.md) for details.

## Development

```bash
git clone https://github.com/sam-phinizy/remindctl-mcp
cd remindctl-mcp
uv sync
uv run pytest
```

## License

MIT
