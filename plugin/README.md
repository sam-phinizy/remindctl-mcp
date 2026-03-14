# remindctl — Claude Code Plugin

Apple Reminders integration for Claude Code. Provides MCP tools for managing reminders and a skill for parsing emails, documents, and threads into structured reminders.

## Prerequisites

- macOS 14+
- [remindctl](https://github.com/steipete/remindctl) installed (`brew install steipete/tap/remindctl`)
- [uv](https://docs.astral.sh/uv/) installed (for uvx)
- Grant Reminders permission: `remindctl authorize`

## Installation

```bash
claude --plugin-dir /path/to/claude-reminders-kit/plugin
```

The plugin automatically configures the `remindctl-mcp` MCP server — no manual MCP setup needed.

## What's Included

### MCP Server (remindctl-mcp)

Full CRUD access to Apple Reminders:

- `get_reminders(filter)` — today, tomorrow, week, overdue, upcoming, completed, all, or a date
- `get_lists()` / `get_list(name)` — list management
- `add_reminder(title, list?, due?, notes?, priority?)` — create reminders
- `edit_reminder(id, title?, due?, notes?, priority?, list?, clear_due?)` — update reminders
- `complete_reminder(ids)` — mark complete
- `delete_reminder(id)` — delete
- `check_status()` — verify permissions

### Skill: text-to-reminders

Parses emails, Slack threads, meeting notes, or any block of text into well-structured reminders.

**Trigger phrases:**
- "parse this email into reminders"
- "extract action items from this"
- "turn this into reminders"
- "create reminders from this"

**What it does:**
1. Extracts action items from the text
2. Consolidates related items (fewer reminders, less noise)
3. Creates short titles with full context in notes
4. Infers due dates from deadlines mentioned in the text
5. Proposes the full list and waits for confirmation before creating

## Usage Examples

Ask Claude:
- "What reminders do I have today?"
- "Add a reminder to review the PR by Friday"
- "Parse this email into reminders" (paste email text)
- "Show my overdue items"
- "Complete reminder 4A83"
