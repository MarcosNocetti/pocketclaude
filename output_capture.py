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


def compute_delta(before: str, after: str) -> str:
    """Return content in after that wasn't in before, based on tail overlap."""
    before_lines = before.rstrip().splitlines()
    after_lines = after.rstrip().splitlines()

    if not before_lines:
        return after.strip()

    # Use last 5 lines of before as anchor to find where new content starts
    tail_size = min(5, len(before_lines))
    tail = before_lines[-tail_size:]

    for i in range(len(after_lines) - tail_size, -1, -1):
        if after_lines[i:i + tail_size] == tail:
            delta_lines = after_lines[i + tail_size:]
            return "\n".join(delta_lines).strip()

    # Fallback: no overlap found, return stripped after
    return after.strip()
