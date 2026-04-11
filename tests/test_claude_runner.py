import pytest
from unittest.mock import patch, MagicMock
import json
import claude_runner


def make_result(stdout="", stderr="", returncode=0):
    m = MagicMock()
    m.stdout = stdout
    m.stderr = stderr
    m.returncode = returncode
    return m


def test_run_claude_returns_result_and_session_id():
    output = json.dumps({"result": "Hello!", "session_id": "abc123", "is_error": False})
    with patch("subprocess.run", return_value=make_result(stdout=output)):
        text, sid = claude_runner.run_claude("hi", "/tmp")
    assert text == "Hello!"
    assert sid == "abc123"


def test_run_claude_includes_resume_when_session_id_given():
    output = json.dumps({"result": "Continuing", "session_id": "abc123", "is_error": False})
    with patch("subprocess.run", return_value=make_result(stdout=output)) as mock_run:
        claude_runner.run_claude("follow up", "/tmp", session_id="abc123")
    cmd = mock_run.call_args[0][0]
    assert "--resume" in cmd
    assert "abc123" in cmd


def test_run_claude_no_resume_when_no_session_id():
    output = json.dumps({"result": "First", "session_id": "new123", "is_error": False})
    with patch("subprocess.run", return_value=make_result(stdout=output)) as mock_run:
        claude_runner.run_claude("first message", "/tmp")
    cmd = mock_run.call_args[0][0]
    assert "--resume" not in cmd


def test_run_claude_handles_error_flag():
    output = json.dumps({"result": "Bad request", "session_id": None, "is_error": True})
    with patch("subprocess.run", return_value=make_result(stdout=output)):
        text, sid = claude_runner.run_claude("bad", "/tmp")
    assert text.startswith("\u274c")


def test_run_claude_handles_invalid_json():
    with patch("subprocess.run", return_value=make_result(stdout="not json", stderr="crash")):
        text, sid = claude_runner.run_claude("bad", "/tmp", session_id="old")
    assert "\u274c" in text
    assert sid == "old"  # preserves original session_id on error
