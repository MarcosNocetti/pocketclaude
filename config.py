import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN: str = os.environ["TELEGRAM_BOT_TOKEN"]
ALLOWED_USER_ID: int = int(os.environ["TELEGRAM_ALLOWED_USER_ID"])
TOTP_SECRET: str = os.environ["TOTP_SECRET"]
UPLOAD_DIR: str = os.path.expanduser(
    os.environ.get("UPLOAD_DIR", "~/uploads")
)
OUTPUT_CAPTURE_DELAY: int = int(os.environ.get("OUTPUT_CAPTURE_DELAY", "3"))
# How long (seconds) a /login session stays valid before requiring a new code.
# Default: 8 hours.
AUTH_SESSION_TTL: int = int(os.environ.get("AUTH_SESSION_TTL", str(8 * 3600)))
CLAUDE_BIN: str = os.environ.get(
    "CLAUDE_BIN",
    os.path.expanduser("~/.nvm/versions/node/v21.7.0/bin/claude"),
)
