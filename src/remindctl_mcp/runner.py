import json
import shutil
import subprocess


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
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
    except subprocess.TimeoutExpired:
        raise RemindctlError("remindctl timed out after 10 seconds")

    if result.returncode != 0:
        raise RemindctlError(result.stderr.strip())

    return json.loads(result.stdout)
