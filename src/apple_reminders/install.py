"""Interactive installer for apple-reminders-py MCP configuration."""

import json
import shutil
import subprocess
import sys
from pathlib import Path


def _uvx_path() -> str:
    """Return the full path to uvx, falling back to 'uvx' if not resolvable."""
    return shutil.which("uvx") or "uvx"


def _mcp_entry() -> dict:
    return {"command": _uvx_path(), "args": ["--refresh", "apple-reminders-py[mcp]"]}


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


def _ensure_remindctl() -> bool:
    """Check for remindctl and offer to install it if missing. Returns True if ready."""
    if shutil.which("remindctl"):
        print("Found remindctl ✓\n")
        return True

    print("remindctl is not installed.\n")

    brew = shutil.which("brew")
    if not brew:
        print("Homebrew is not installed either.")
        print("Install Homebrew first: https://brew.sh")
        print("Then run: brew install steipete/tap/remindctl\n")
        answer = input("Continue anyway? (y/N): ").strip().lower()
        return answer == "y"

    answer = input("Install remindctl via Homebrew? (Y/n): ").strip().lower()
    if answer in ("", "y"):
        print()
        result = subprocess.run([brew, "install", "steipete/tap/remindctl"])
        if result.returncode != 0:
            print("\n⚠️  Homebrew install failed. You can install manually:")
            print("   brew install steipete/tap/remindctl\n")
            answer = input("Continue anyway? (y/N): ").strip().lower()
            return answer == "y"
        print("\nremindctl installed ✓")
        print("Run `remindctl authorize` in your terminal to grant Reminders access.\n")
        return True
    else:
        print("Skipping remindctl install.\n")
        return True


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


def _install_to(label: str, path: Path, force: bool = False) -> None:
    config = _load_json(path)
    if not config:
        config = {}

    servers = config.setdefault("mcpServers", {})

    if "remindctl" in servers and not force:
        print(f"  ✓ remindctl already configured in {label} (use --force to overwrite)")
        return

    already_existed = "remindctl" in servers
    servers["remindctl"] = _mcp_entry()
    _write_config(path, config)
    action = "Updated" if already_existed else "Added"
    print(f"  ✓ {action} remindctl in {label} ({path})")


def run_installer(force: bool = False) -> None:
    print("apple-reminders-py MCP installer")
    print("-" * 40)

    uvx = _uvx_path()
    if shutil.which("uvx"):
        print(f"Found uvx at: {uvx}")
    else:
        print("⚠️  uvx not found on PATH — config will use 'uvx' as the command.")
        print("   Install uv from https://docs.astral.sh/uv/ first.")
    print()

    if not _ensure_remindctl():
        print("Aborted.")
        sys.exit(1)

    if force:
        print("⚡ Force mode — existing entries will be overwritten.\n")

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
        _install_to(label, path, force=force)

    print("\nDone! Restart any open Claude clients to load the MCP server.")
    if not shutil.which("remindctl"):
        print("Remember to install remindctl and run `remindctl authorize` in your terminal.")
