import subprocess
from typing import Optional

_active_session: Optional[str] = None
_output_delay: int = 3


def get_active() -> Optional[str]:
    return _active_session


def set_active(name: Optional[str]) -> None:
    global _active_session
    _active_session = name


def get_delay() -> int:
    return _output_delay


def set_delay(seconds: int) -> None:
    global _output_delay
    _output_delay = seconds


def session_exists(name: str) -> bool:
    result = subprocess.run(
        ["tmux", "has-session", "-t", name],
        capture_output=True
    )
    return result.returncode == 0


def new_session(name: str) -> bool:
    """Create a new detached tmux session and activate it. Returns False if already exists."""
    if session_exists(name):
        return False
    result = subprocess.run(
        ["tmux", "new-session", "-d", "-s", name],
        capture_output=True
    )
    if result.returncode == 0:
        set_active(name)
        return True
    return False


def attach_session(name: str) -> bool:
    """Set an existing session as active. Returns False if not found."""
    if not session_exists(name):
        return False
    set_active(name)
    return True


def kill_session(name: str) -> bool:
    """Kill a tmux session. Clears active if it was the active one."""
    if not session_exists(name):
        return False
    result = subprocess.run(
        ["tmux", "kill-session", "-t", name],
        capture_output=True
    )
    if result.returncode == 0:
        if _active_session == name:
            set_active(None)
        return True
    return False


def list_sessions() -> list[str]:
    result = subprocess.run(
        ["tmux", "list-sessions", "-F", "#{session_name}"],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        return []
    return [s for s in result.stdout.strip().splitlines() if s]


def send_keys(session_name: str, text: str) -> bool:
    result = subprocess.run(
        ["tmux", "send-keys", "-t", session_name, text, "Enter"],
        capture_output=True
    )
    return result.returncode == 0
