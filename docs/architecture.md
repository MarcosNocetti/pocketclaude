# Architecture — telegram-pc-bot

## Flow

```
[Phone / Telegram App]
        │
        │  HTTPS (Telegram API)
        ▼
[Telegram Servers]
        │
        │  polling (python-telegram-bot)
        ▼
[Bot Process — bot.py]
        │
        ├─ Auth check (TOTP via auth_manager.py)
        │
        ├─ /send  → file_manager.py → reply_document()
        ├─ /ls    → file_manager.py → list_dir()
        ├─ upload → file_manager.py → download_to_drive()
        │
        └─ text/command → claude_runner.py
                │
                │  subprocess: claude -p "<message>" --output-format json
                │              [--resume <session_id>]
                ▼
        [Claude Code CLI]
                │
                └─ JSON response → session_manager.py (persist session_id)
                        │
                        ▼
                [Telegram reply to phone]
```

## Components

| Module | Responsibility |
|---|---|
| `bot.py` | Entry point, command/message routing, auth decorator |
| `auth_manager.py` | TOTP 2FA — verify code, session TTL |
| `claude_runner.py` | Invoke `claude -p` subprocess, parse JSON response |
| `session_manager.py` | Named sessions with cwd and Claude session_id |
| `file_manager.py` | Send files to Telegram, receive uploads, list directories |
| `queue_manager.py` | Queue messages when Claude rate-limited, schedule retry |
| `config.py` | Load all env variables with sensible defaults |

## Security

- Only one `TELEGRAM_ALLOWED_USER_ID` is accepted — all other users are silently ignored
- Every command (except `/login`) requires an active TOTP session (default TTL: 8h)
- Bot token and TOTP secret are never in source code — `.env` only
