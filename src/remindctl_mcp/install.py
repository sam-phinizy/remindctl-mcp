"""Interactive installer for remindctl-mcp MCP configuration."""

import json
import sys
from pathlib import Path

MCP_ENTRY = {"command": "uvx", "args": ["remindctl-mcp"]}

TARGETS = {
    "1": (
        "Claude Desktop",
        Path.home() / "Library/Application Support/Claude/claude_desktop_config.json",
    ),
    "2": (
        "Claude Code — project (.mcp.json in current directory)",
        Path.cwd() / ".mcp.json",
    ),
    "3": (
        "Claude Code — user (~/.claude.json)",
        Path.home() / ".claude.json",
    ),
}


def _load_json(path: Path) -> dict:
    if path.exists():
        try:
            return json.loads(path.read_text())
        except json.JSONDecodeError:
            print(f"  ⚠️  {path} contains invalid JSON — skipping.")
            return {}
    return {}


def _write_config(path: Path, config: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(config, indent=2) + "\n")


def _install_to(label: str, path: Path) -> None:
    config = _load_json(path)
    if not config:
        config = {}

    servers = config.setdefault("mcpServers", {})

    if "remindctl" in servers:
        print(f"  ✓ remindctl already configured in {label}")
        return

    servers["remindctl"] = MCP_ENTRY
    _write_config(path, config)
    print(f"  ✓ Added remindctl to {label} ({path})")


def run_installer() -> None:
    print("remindctl-mcp installer")
    print("-" * 40)
    print("Where would you like to install?\n")

    for key, (label, path) in TARGETS.items():
        print(f"  [{key}] {label}")
    print("  [a] All of the above")
    print("  [q] Quit\n")

    raw = input("Enter choices (e.g. 1 2 or a): ").strip().lower()

    if not raw or raw == "q":
        print("Aborted.")
        sys.exit(0)

    if raw == "a":
        choices = list(TARGETS.keys())
    else:
        choices = [c for c in raw.split() if c in TARGETS]
        if not choices:
            print("No valid choices — exiting.")
            sys.exit(1)

    print()
    for key in choices:
        label, path = TARGETS[key]
        _install_to(label, path)

    print("\nDone! Restart any open Claude clients to load the MCP server.")
