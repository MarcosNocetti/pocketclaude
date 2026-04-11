import json
import os
import subprocess
from typing import Optional

CLAUDE_BIN = os.path.expanduser("~/.nvm/versions/node/v21.7.0/bin/claude")


def run_claude(
    message: str,
    cwd: str,
    session_id: Optional[str] = None,
) -> tuple:
    """
    Run claude -p and return (response_text, new_session_id).
    Uses --resume if session_id is provided.
    """
    cmd = [
        CLAUDE_BIN, "-p", message,
        "--dangerously-skip-permissions",
        "--output-format", "json",
    ]
    if session_id:
        cmd += ["--resume", session_id]

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=os.path.expanduser(cwd),
    )

    try:
        data = json.loads(result.stdout)
        text = data.get("result", "").strip()
        new_id = data.get("session_id")
        if data.get("is_error"):
            return f"\u274c {text or 'Erro desconhecido'}", session_id
        return text or "(sem resposta)", new_id
    except (json.JSONDecodeError, KeyError):
        error = (result.stderr or result.stdout).strip()
        return f"\u274c Erro: {error[:500]}", session_id
