"""
Persistent message queue for rate-limited Claude requests.

Messages are stored in queue.json and dispatched automatically
when Claude's usage limit resets.
"""

import json
import os
import re
from datetime import datetime, timedelta
from typing import Optional

import pytz

QUEUE_FILE = os.path.join(os.path.dirname(__file__), "queue.json")
TZ = pytz.timezone("America/Sao_Paulo")

# Matches examples like:
# "resets 11pm", "resets at 11:30pm", "try again at 11 pm", "until 11pm"
_RESET_RE = re.compile(
    r"(?:resets?|try again(?:\s+(?:after|at))?|available again|until)\s*(?:at\s*)?"
    r"(\d{1,2})(?::(\d{2}))?\s*(am|pm)",
    re.IGNORECASE,
)

RATE_LIMIT_PATTERNS = (
    re.compile(r"you(?: have|'ve)\s+hit\s+your\s+limit", re.IGNORECASE),
    re.compile(r"out of (?:extra )?usage", re.IGNORECASE),
    re.compile(r"usage limit", re.IGNORECASE),
    re.compile(r"rate limit", re.IGNORECASE),
    re.compile(r"too many requests", re.IGNORECASE),
    re.compile(r"\b429\b", re.IGNORECASE),
    re.compile(r"credit balance is too low", re.IGNORECASE),
    re.compile(r"insufficient (?:credits|tokens?)", re.IGNORECASE),
    re.compile(r"(?:no|without)\s+(?:credits|tokens?)", re.IGNORECASE),
    re.compile(r"token limit", re.IGNORECASE),
)


def _load() -> list[dict]:
    if not os.path.exists(QUEUE_FILE):
        return []
    try:
        with open(QUEUE_FILE) as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return []


def _save(queue: list[dict]) -> None:
    with open(QUEUE_FILE, "w") as f:
        json.dump(queue, f, indent=2, ensure_ascii=False)


def parse_reset_time(response: str) -> Optional[datetime]:
    """Extract reset datetime from Claude's rate-limit message."""
    m = _RESET_RE.search(response)
    if not m:
        return None
    hour = int(m.group(1))
    minute = int(m.group(2)) if m.group(2) else 0
    period = m.group(3).lower()
    if period == "pm" and hour != 12:
        hour += 12
    elif period == "am" and hour == 12:
        hour = 0

    now = datetime.now(TZ)
    reset = TZ.localize(datetime(now.year, now.month, now.day, hour, minute, 0))
    if reset <= now:
        reset += timedelta(days=1)
    return reset


def is_rate_limited(response: str) -> bool:
    return any(pattern.search(response) for pattern in RATE_LIMIT_PATTERNS)


def enqueue(
    chat_id: int,
    session_name: str,
    cwd: str,
    claude_id: Optional[str],
    text: str,
    reset_at: Optional[datetime],
) -> int:
    """Add a message to the queue. Returns the new queue length."""
    queue = _load()
    queue.append({
        "chat_id": chat_id,
        "session_name": session_name,
        "cwd": cwd,
        "claude_id": claude_id,
        "text": text,
        "reset_at": reset_at.isoformat() if reset_at else None,
        "queued_at": datetime.now(TZ).isoformat(),
    })
    _save(queue)
    return len(queue)


def list_messages() -> list[dict]:
    return _load()


def remove_message(index: int) -> bool:
    """Remove message by 1-based index. Returns True if removed."""
    queue = _load()
    if index < 1 or index > len(queue):
        return False
    queue.pop(index - 1)
    _save(queue)
    return True


def clear() -> int:
    """Clear all queued messages. Returns count removed."""
    queue = _load()
    count = len(queue)
    _save([])
    return count


def pop_all() -> list[dict]:
    """Return and remove all queued messages."""
    queue = _load()
    _save([])
    return queue
