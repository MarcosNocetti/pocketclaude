import json
import os
from typing import Optional

SESSION_FILE = os.path.expanduser("~/telegram-pc-bot/sessions.json")
ACTIVE_SESSION_FILE = os.path.expanduser("~/telegram-pc-bot/active_session.json")

_active_session: Optional[str] = None
_sessions: dict = {}  # name -> {"claude_id": str|None, "cwd": str}


def _load() -> None:
    global _sessions, _active_session
    if os.path.exists(SESSION_FILE):
        try:
            with open(SESSION_FILE) as f:
                _sessions = json.load(f)
        except (json.JSONDecodeError, OSError):
            _sessions = {}
    if os.path.exists(ACTIVE_SESSION_FILE):
        try:
            with open(ACTIVE_SESSION_FILE) as f:
                active = json.load(f).get("active")
                _active_session = active if active in _sessions else None
        except (json.JSONDecodeError, OSError, AttributeError):
            _active_session = None


def _save() -> None:
    with open(SESSION_FILE, "w") as f:
        json.dump(_sessions, f, indent=2)


def _save_active() -> None:
    with open(ACTIVE_SESSION_FILE, "w") as f:
        json.dump({"active": _active_session}, f, indent=2)


_load()


def get_active() -> Optional[str]:
    return _active_session


def set_active(name: Optional[str]) -> None:
    global _active_session
    _active_session = name
    _save_active()


def new_session(name: str, cwd: str = "~") -> bool:
    """Register a new session. Returns False if name already exists."""
    if name in _sessions:
        return False
    _sessions[name] = {"claude_id": None, "cwd": os.path.expanduser(cwd)}
    _save()
    set_active(name)
    return True


def attach_session(name: str) -> bool:
    """Set session as active. Returns False if not found."""
    if name not in _sessions:
        return False
    set_active(name)
    return True


def kill_session(name: str) -> bool:
    """Remove a session. Returns False if not found."""
    global _active_session
    if name not in _sessions:
        return False
    del _sessions[name]
    _save()
    if _active_session == name:
        set_active(None)
    return True


def list_sessions() -> list:
    return list(_sessions.keys())


def get_session_cwd(name: str) -> str:
    return _sessions.get(name, {}).get("cwd", os.path.expanduser("~"))


def get_claude_id(name: str) -> Optional[str]:
    return _sessions.get(name, {}).get("claude_id")


def set_claude_id(name: str, claude_id: str) -> None:
    if name in _sessions:
        _sessions[name]["claude_id"] = claude_id
        _save()
