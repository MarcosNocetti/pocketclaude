import re
import subprocess

ANSI_ESCAPE = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')


def strip_ansi(text: str) -> str:
    return ANSI_ESCAPE.sub('', text)


def capture_pane(session_name: str) -> str:
    result = subprocess.run(
        ["tmux", "capture-pane", "-p", "-t", session_name],
        capture_output=True, text=True
    )
    return strip_ansi(result.stdout)


def capture_pane_recent(session_name: str, lines: int = 30) -> str:
    """Capture last N non-empty lines of the pane. More reliable than delta."""
    result = subprocess.run(
        ["tmux", "capture-pane", "-p", "-S", "-200", "-t", session_name],
        capture_output=True, text=True
    )
    content = strip_ansi(result.stdout)
    non_empty = [l for l in content.splitlines() if l.strip()]
    return "\n".join(non_empty[-lines:])


def compute_delta(before: str, after: str) -> str:
    """Return content in after that wasn't in before, based on tail overlap."""
    before_lines = before.rstrip().splitlines()
    after_lines = after.rstrip().splitlines()

    if not before_lines:
        return after.strip()

    # Use last 5 lines of before as anchor to find where new content starts
    tail_size = min(5, len(before_lines))
    tail = before_lines[-tail_size:]

    # Search forward to find first occurrence of tail, then return what follows it
    found_tail = False
    for i in range(len(after_lines) - tail_size + 1):
        if after_lines[i:i + tail_size] == tail:
            found_tail = True
            delta_lines = after_lines[i + tail_size:]
            result = "\n".join(delta_lines).strip()
            if result:
                return result

    if found_tail:
        return ""  # tail found but nothing new after it

    # Fallback: content changed completely, return stripped after
    return after.strip()
