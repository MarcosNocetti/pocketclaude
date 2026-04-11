import os
from pathlib import Path

_upload_dir: str = os.path.expanduser("~/uploads")


def set_upload_dir(path: str) -> None:
    global _upload_dir
    _upload_dir = path
    Path(_upload_dir).mkdir(parents=True, exist_ok=True)


def list_dir(path: str) -> str:
    expanded = os.path.expanduser(path)
    try:
        entries = list(os.scandir(expanded))
        if not entries:
            return "(empty)"
        lines = []
        for e in sorted(entries, key=lambda x: (not x.is_dir(), x.name.lower())):
            prefix = "📁" if e.is_dir() else "📄"
            lines.append(f"{prefix} {e.name}")
        return "\n".join(lines)
    except FileNotFoundError:
        return f"❌ Caminho não encontrado: {path}"
    except PermissionError:
        return f"❌ Sem permissão: {path}"


def resolve_send_path(path: str) -> tuple[str | None, str | None]:
    """Return (absolute_path, None) on success, or (None, error_message) on failure."""
    expanded = os.path.expanduser(path)
    if not os.path.exists(expanded):
        return None, f"❌ Arquivo não encontrado: {path}"
    if not os.path.isfile(expanded):
        return None, f"❌ Não é um arquivo: {path}"
    if os.path.getsize(expanded) > 50 * 1024 * 1024:
        return None, "❌ Arquivo muito grande (limite: 50MB)"
    return expanded, None


def upload_destination(filename: str) -> str:
    Path(_upload_dir).mkdir(parents=True, exist_ok=True)
    return os.path.join(_upload_dir, filename)
