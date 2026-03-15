import json
from unittest.mock import AsyncMock, patch

import pytest

from apple_reminders.exceptions import (
    RemindersError,
    RemindersNotFoundError,
    RemindersTimeoutError,
)
from apple_reminders.runner import run_remindctl


@pytest.fixture
def mock_binary():
    with patch("apple_reminders.runner.shutil.which", return_value="/usr/local/bin/remindctl") as m:
        yield m


def _make_process(stdout: str = "", stderr: str = "", returncode: int = 0):
    proc = AsyncMock()
    proc.communicate.return_value = (stdout.encode(), stderr.encode())
    proc.returncode = returncode
    proc.kill = AsyncMock()
    return proc


@pytest.mark.asyncio
async def test_returns_list(mock_binary):
    payload = [{"id": "1", "title": "Buy milk"}]
    proc = _make_process(stdout=json.dumps(payload))
    with patch("apple_reminders.runner.asyncio.create_subprocess_exec", return_value=proc):
        result = await run_remindctl(["list"])
    assert result == payload


@pytest.mark.asyncio
async def test_returns_dict(mock_binary):
    payload = {"id": "42", "title": "Take out trash"}
    proc = _make_process(stdout=json.dumps(payload))
    with patch("apple_reminders.runner.asyncio.create_subprocess_exec", return_value=proc):
        result = await run_remindctl(["get", "42"])
    assert result == payload


@pytest.mark.asyncio
async def test_raises_when_binary_not_found():
    with patch("apple_reminders.runner.shutil.which", return_value=None):
        with pytest.raises(RemindersNotFoundError, match="not found"):
            await run_remindctl(["list"])


@pytest.mark.asyncio
async def test_raises_on_nonzero_exit(mock_binary):
    proc = _make_process(stderr="Permission denied", returncode=1)
    with patch("apple_reminders.runner.asyncio.create_subprocess_exec", return_value=proc):
        with pytest.raises(RemindersError, match="Permission denied"):
            await run_remindctl(["list"])


@pytest.mark.asyncio
async def test_raises_on_timeout(mock_binary):
    import asyncio as aio

    proc = _make_process()

    with patch("apple_reminders.runner.asyncio.create_subprocess_exec", return_value=proc):
        with patch("apple_reminders.runner.asyncio.wait_for", side_effect=aio.TimeoutError()):
            with pytest.raises(RemindersTimeoutError, match="timed out"):
                await run_remindctl(["list"])


@pytest.mark.asyncio
async def test_appends_json_flag(mock_binary):
    payload = []
    proc = _make_process(stdout=json.dumps(payload))
    captured = {}

    async def fake_exec(*args, **kwargs):
        captured["cmd"] = args
        return proc

    with patch("apple_reminders.runner.asyncio.create_subprocess_exec", side_effect=fake_exec):
        await run_remindctl(["list", "--filter", "today"])

    assert captured["cmd"][-1] == "--json"


@pytest.mark.asyncio
async def test_raises_on_invalid_json(mock_binary):
    proc = _make_process(stdout="not valid json")
    with patch("apple_reminders.runner.asyncio.create_subprocess_exec", return_value=proc):
        with pytest.raises(RemindersError, match="invalid JSON"):
            await run_remindctl(["list"])
