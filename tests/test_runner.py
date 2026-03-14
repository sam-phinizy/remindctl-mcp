import json
import subprocess
from unittest.mock import MagicMock, patch

import pytest

from remindctl_mcp.runner import RemindctlError, run_remindctl


def make_completed_process(stdout="", stderr="", returncode=0):
    result = MagicMock()
    result.stdout = stdout
    result.stderr = stderr
    result.returncode = returncode
    return result


def test_returns_list_on_success():
    payload = [{"id": "1", "title": "Buy milk"}]
    with patch("remindctl_mcp.runner.shutil.which", return_value="/usr/local/bin/remindctl"), patch(
        "remindctl_mcp.runner.subprocess.run", return_value=make_completed_process(stdout=json.dumps(payload))
    ):
        result = run_remindctl(["list"])
    assert result == payload


def test_returns_dict_on_success():
    payload = {"id": "42", "title": "Take out trash"}
    with patch("remindctl_mcp.runner.shutil.which", return_value="/usr/local/bin/remindctl"), patch(
        "remindctl_mcp.runner.subprocess.run", return_value=make_completed_process(stdout=json.dumps(payload))
    ):
        result = run_remindctl(["get", "42"])
    assert result == payload


def test_raises_when_binary_not_found():
    with patch("remindctl_mcp.runner.shutil.which", return_value=None):
        with pytest.raises(RemindctlError) as exc_info:
            run_remindctl(["list"])
    assert "not found" in str(exc_info.value)


def test_raises_on_nonzero_exit():
    with patch("remindctl_mcp.runner.shutil.which", return_value="/usr/local/bin/remindctl"), patch(
        "remindctl_mcp.runner.subprocess.run",
        return_value=make_completed_process(stderr="Permission denied", returncode=1),
    ):
        with pytest.raises(RemindctlError) as exc_info:
            run_remindctl(["list"])
    assert "Permission denied" in str(exc_info.value)


def test_raises_on_timeout():
    with patch("remindctl_mcp.runner.shutil.which", return_value="/usr/local/bin/remindctl"), patch(
        "remindctl_mcp.runner.subprocess.run",
        side_effect=subprocess.TimeoutExpired(cmd="remindctl", timeout=10),
    ):
        with pytest.raises(RemindctlError) as exc_info:
            run_remindctl(["list"])
    assert "timed out" in str(exc_info.value)


def test_appends_json_flag():
    payload = []
    captured = {}

    def fake_run(cmd, **kwargs):
        captured["cmd"] = cmd
        return make_completed_process(stdout=json.dumps(payload))

    with patch("remindctl_mcp.runner.shutil.which", return_value="/usr/local/bin/remindctl"), patch(
        "remindctl_mcp.runner.subprocess.run", side_effect=fake_run
    ):
        run_remindctl(["list", "--filter", "today"])

    assert captured["cmd"][-1] == "--json", "last arg must be --json"


def test_raises_on_invalid_json():
    with patch("remindctl_mcp.runner.shutil.which", return_value="/usr/local/bin/remindctl"), patch(
        "remindctl_mcp.runner.subprocess.run",
        return_value=make_completed_process(stdout="not valid json"),
    ):
        with pytest.raises(RemindctlError) as exc_info:
            run_remindctl(["list"])
    assert "invalid JSON" in str(exc_info.value)
