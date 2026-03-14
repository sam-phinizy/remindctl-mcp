---
name: text-to-reminders
description: This skill should be used when the user asks to "parse this email into reminders", "extract action items from this", "turn this into reminders", "convert this email to tasks", "add reminders from this thread", "parse this document for action items", or pastes a large block of text (email, Slack thread, meeting notes, document) and asks for reminders to be created from it. Handles extraction, consolidation, smart due dates, and structured note-taking.
version: 0.1.0
---

# Text to Reminders

Parse emails, documents, Slack threads, or any block of text into well-structured Apple Reminders — with short titles, full context in notes, and due dates extracted from the text.

## Core Principles

**Short titles, rich notes.** A good reminder title is scannable in a list: "Call Sarah re: contract" not "Call Sarah to discuss the contract renewal terms before the end of Q2". Move all context into the notes field.

**Extract, don't invent.** Only create reminders for explicit action items or commitments. Don't infer tasks from background context.

**Consolidate before creating.** Related items belonging to the same project or person should be grouped into one reminder where possible. Five reminders about the same project create noise.

**Propose before acting.** Always show the proposed reminder list and get confirmation before calling any MCP tools.

## Workflow

### Step 1: Read the Text Carefully

Scan the full text for:
- Explicit action items ("please send", "can you", "we need to", "don't forget")
- Implicit commitments ("I'll follow up", "let's schedule", "we agreed")
- Deadlines and dates (absolute: "by March 20", relative: "end of week", "before the call")
- Named owners — only capture items the user is responsible for

### Step 2: Extract Raw Action Items

List every candidate action item with:
- The raw task as stated in the text
- The deadline or date hint (if any)
- The relevant context (who asked, what for, why it matters)

### Step 3: Consolidate

Apply these consolidation rules:
- Merge items that are sub-tasks of the same deliverable into one reminder with all steps in the notes
- Merge follow-ups about the same person/project into one reminder
- Keep items separate only if they have different owners, hard deadlines, or unrelated scope

Aim for the fewest reminders that cover all action items without losing information.

### Step 4: Propose the Reminder List

Present a structured proposal before creating anything:

```
Here's what I found — 4 reminders (consolidated from 7 action items):

1. **Reply to Sarah re: contract terms**
   List: Work
   Due: March 20
   Notes: She needs the redlined version before her board meeting. Key points to address: liability cap (§4.2), IP ownership (§7), payment terms (net-30 → net-15).

2. **Schedule design review with Jake**
   List: Work
   Due: this week
   Notes: Mentioned in thread from March 14. Needs to happen before the sprint kickoff. Suggested times: Tue/Thu afternoon.

3. **Send Q1 report to finance**
   List: Work
   Due: March 31
   Notes: End-of-quarter deadline. Finance contact: billing@acme.com. Include headcount delta and budget variance.

4. **Follow up with vendor on pricing**
   List: Work
   Due: (none found)
   Notes: They said they'd have updated pricing "by end of month". If no response by March 25, escalate to procurement.

Shall I create these? Or adjust any before I do?
```

### Step 5: Handle User Adjustments

If the user wants changes, update the proposal in-place. Common adjustments:
- Change list assignment
- Adjust or remove a due date
- Split or merge items
- Edit a title or notes

Re-present only the changed items for confirmation, not the full list.

### Step 6: Create the Reminders

Once confirmed, call `add_reminder` for each item in sequence:
- Pass `title`, `reminder_list`, `due` (if present), and `notes`
- Use `priority: high` only for items with hard deadlines under 48 hours or explicitly marked urgent
- After all are created, summarise: "Created 4 reminders in Work."

## Due Date Extraction

| Text clue | Infer as |
|-----------|----------|
| "by [date]", "before [date]", "on [date]" | That date |
| "end of week" / "this week" | Friday of current week |
| "end of month" | Last day of current month |
| "tomorrow", "next Tuesday" | Relative to today |
| "ASAP", "urgent", "immediately" | Today |
| "soon", "eventually", "at some point" | No due date — note in text |
| No date mentioned | No due date |

When the date is ambiguous or relative, state your interpretation in the proposal: "Due: Friday Mar 21 (interpreted from 'end of week')" so the user can correct it.

## Notes Field Best Practices

Good notes give future-you enough context to act without re-reading the source:

- **Who**: who sent the request, who it affects
- **Why**: the purpose or stakes
- **What exactly**: specific deliverables, numbers, links, quoted text if important
- **Dependencies**: what needs to happen first
- **Contact info**: email addresses, names mentioned

Avoid padding. If the context is obvious from the title, keep notes short.

## List Assignment

If the user hasn't specified a default list, call `get_lists` first and infer from context:
- Work emails → professional lists
- Personal correspondence → personal lists
- Ambiguous → propose a list and ask

## Additional Resources

- **`references/examples.md`** — worked examples of email → reminder conversions with before/after comparisons
