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
