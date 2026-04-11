import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN: str = os.environ["TELEGRAM_BOT_TOKEN"]
ALLOWED_USER_ID: int = int(os.environ["TELEGRAM_ALLOWED_USER_ID"])
UPLOAD_DIR: str = os.path.expanduser(
    os.environ.get("UPLOAD_DIR", "~/uploads")
)
OUTPUT_CAPTURE_DELAY: int = int(os.environ.get("OUTPUT_CAPTURE_DELAY", "3"))
