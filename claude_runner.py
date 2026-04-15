import json
import os
import subprocess
from typing import Optional

import config as _config
CLAUDE_BIN = _config.CLAUDE_BIN
DEBUG_FILE = os.path.join(os.path.dirname(__file__), "claude_debug.log")
CLAUDE_TIMEOUT_SECONDS = int(os.getenv("CLAUDE_TIMEOUT_SECONDS", "1800"))


def _debug_log(payload: dict) -> None:
    try:
        with open(DEBUG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")
    except OSError:
        pass


def _build_cmd(message: str, session_id: Optional[str]) -> list[str]:
    cmd = [
        CLAUDE_BIN, "-p", message,
        "--dangerously-skip-permissions",
        "--output-format", "json",
    ]
    if session_id:
        cmd += ["--resume", session_id]
    return cmd


def _execute_claude(cmd: list[str], cwd: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=os.path.expanduser(cwd),
        timeout=CLAUDE_TIMEOUT_SECONDS,
    )


def run_claude(
    message: str,
    cwd: str,
    session_id: Optional[str] = None,
) -> tuple:
    """
    Run claude -p and return (response_text, new_session_id).
    Uses --resume if session_id is provided.
    """
    attempts = [session_id]
    if session_id:
        attempts.append(None)

    last_error = None

    for attempt_session_id in attempts:
        cmd = _build_cmd(message, attempt_session_id)
        try:
            result = _execute_claude(cmd, cwd)
        except subprocess.TimeoutExpired as exc:
            last_error = f"Timeout após {CLAUDE_TIMEOUT_SECONDS}s"
            _debug_log({
                "cwd": os.path.expanduser(cwd),
                "session_id": attempt_session_id,
                "message_preview": message[:200],
                "timeout": True,
                "stdout_preview": ((exc.stdout or "") if isinstance(exc.stdout, str) else "")[:1000],
                "stderr_preview": ((exc.stderr or "") if isinstance(exc.stderr, str) else "")[:1000],
            })
            continue

        debug_payload = {
            "cwd": os.path.expanduser(cwd),
            "session_id": attempt_session_id,
            "message_preview": message[:200],
            "returncode": result.returncode,
            "stdout_preview": (result.stdout or "")[:1000],
            "stderr_preview": (result.stderr or "")[:1000],
        }

        try:
            data = json.loads(result.stdout)
            text = data.get("result", "").strip()
            new_id = data.get("session_id")
            debug_payload.update({
                "parsed": True,
                "is_error": data.get("is_error"),
                "result_preview": text[:1000],
                "new_session_id": new_id,
            })
            _debug_log(debug_payload)
            if data.get("is_error"):
                return f"\u274c {text or 'Erro desconhecido'}", attempt_session_id
            return text or "(sem resposta)", new_id
        except (json.JSONDecodeError, KeyError):
            error = (result.stderr or result.stdout).strip()
            debug_payload.update({
                "parsed": False,
                "fallback_error_preview": error[:1000],
            })
            _debug_log(debug_payload)
            last_error = error[:500] or "Erro desconhecido"
            if not session_id or attempt_session_id is None:
                return f"\u274c Erro: {last_error}", attempt_session_id

    return f"\u274c Erro: {last_error or 'Erro desconhecido'}", session_id
