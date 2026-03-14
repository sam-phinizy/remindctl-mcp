import json
import shutil
import subprocess

_TIMEOUT_SECONDS = 10


class RemindctlError(Exception):
    """Raised when remindctl cannot be found or returns an error."""


def run_remindctl(args: list[str]) -> dict | list:
    """Run remindctl with the given arguments and return parsed JSON output.

    Args:
        args: Command-line arguments to pass to remindctl (excluding the binary
              name and the --json flag, which are always added automatically).

    Returns:
        Parsed JSON response as a dict or list.

    Raises:
        RemindctlError: If the binary is not found, times out, or exits non-zero.
    """
    binary = shutil.which("remindctl")
    if binary is None:
        raise RemindctlError(
            "remindctl not found. Install from https://github.com/steipete/remindctl"
        )

    cmd = [binary] + args + ["--json"]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=_TIMEOUT_SECONDS)
    except subprocess.TimeoutExpired:
        raise RemindctlError(f"remindctl timed out after {_TIMEOUT_SECONDS} seconds")

    if result.returncode != 0:
        raise RemindctlError(result.stderr.strip())

    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as e:
        raise RemindctlError(f"remindctl returned invalid JSON: {e}")
