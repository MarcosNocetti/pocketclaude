import time
from typing import Optional

import pyotp

import config

# How long (seconds) a successful login stays valid. Default: 8 hours.
SESSION_TTL = int(getattr(config, "AUTH_SESSION_TTL", 8 * 3600))

_authenticated_until: Optional[float] = None


def _totp() -> pyotp.TOTP:
    return pyotp.TOTP(config.TOTP_SECRET)


def is_authenticated() -> bool:
    if _authenticated_until is None:
        return False
    return time.time() < _authenticated_until


def verify_and_login(code: str) -> bool:
    """Verify a TOTP code. Returns True and marks session as authenticated on success."""
    global _authenticated_until
    if _totp().verify(code, valid_window=2):
        _authenticated_until = time.time() + SESSION_TTL
        return True
    return False


def logout() -> None:
    global _authenticated_until
    _authenticated_until = None


def remaining() -> str:
    """Human-readable time remaining in the authenticated session."""
    if not is_authenticated():
        return "não autenticado"
    secs = int(_authenticated_until - time.time())
    h, m = divmod(secs, 3600)
    m //= 60
    return f"{h}h {m}m restantes"


def provisioning_uri(name: str = "telegram-pc-bot", issuer: str = "bot") -> str:
    return _totp().provisioning_uri(name=name, issuer_name=issuer)
