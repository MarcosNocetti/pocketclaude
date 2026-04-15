import json
import os
import pytest
import tempfile
import session_manager


@pytest.fixture(autouse=True)
def reset_state(tmp_path, monkeypatch):
    """Reset session manager state and use temp file for each test."""
    monkeypatch.setattr(session_manager, "SESSION_FILE", str(tmp_path / "sessions.json"))
    monkeypatch.setattr(session_manager, "ACTIVE_SESSION_FILE", str(tmp_path / "active_session.json"))
    monkeypatch.setattr(session_manager, "_sessions", {})
    monkeypatch.setattr(session_manager, "_active_session", None)
    yield


def test_new_session_creates_and_activates():
    assert session_manager.new_session("test") is True
    assert session_manager.get_active() == "test"


def test_new_session_fails_if_exists():
    session_manager.new_session("test")
    assert session_manager.new_session("test") is False


def test_new_session_stores_cwd():
    session_manager.new_session("test", "/tmp")
    assert session_manager.get_session_cwd("test") == "/tmp"


def test_new_session_default_cwd():
    session_manager.new_session("test")
    assert session_manager.get_session_cwd("test") == os.path.expanduser("~")


def test_attach_sets_active():
    session_manager.new_session("a")
    session_manager.new_session("b")
    assert session_manager.attach_session("a") is True
    assert session_manager.get_active() == "a"


def test_attach_fails_if_not_found():
    assert session_manager.attach_session("ghost") is False


def test_kill_removes_session():
    session_manager.new_session("test")
    assert session_manager.kill_session("test") is True
    assert "test" not in session_manager.list_sessions()


def test_kill_clears_active_if_was_active():
    session_manager.new_session("test")
    session_manager.kill_session("test")
    assert session_manager.get_active() is None


def test_kill_preserves_other_active():
    session_manager.new_session("a")
    session_manager.new_session("b")
    session_manager.set_active("a")
    session_manager.kill_session("b")
    assert session_manager.get_active() == "a"


def test_list_sessions():
    session_manager.new_session("a")
    session_manager.new_session("b")
    assert set(session_manager.list_sessions()) == {"a", "b"}


def test_claude_id_round_trip():
    session_manager.new_session("test")
    assert session_manager.get_claude_id("test") is None
    session_manager.set_claude_id("test", "abc123")
    assert session_manager.get_claude_id("test") == "abc123"


def test_persistence(tmp_path, monkeypatch):
    session_file = str(tmp_path / "sessions.json")
    active_file = str(tmp_path / "active_session.json")
    monkeypatch.setattr(session_manager, "SESSION_FILE", session_file)
    monkeypatch.setattr(session_manager, "ACTIVE_SESSION_FILE", active_file)
    monkeypatch.setattr(session_manager, "_sessions", {})
    monkeypatch.setattr(session_manager, "_active_session", None)
    session_manager.new_session("persist", "/home/test")
    session_manager.set_claude_id("persist", "xyz789")
    # Simulate reload
    monkeypatch.setattr(session_manager, "_sessions", {})
    monkeypatch.setattr(session_manager, "_active_session", None)
    session_manager._load()
    assert "persist" in session_manager.list_sessions()
    assert session_manager.get_claude_id("persist") == "xyz789"
    assert session_manager.get_session_cwd("persist") == "/home/test"
    assert session_manager.get_active() == "persist"
