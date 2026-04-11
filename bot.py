import asyncio
import logging
import time
from functools import wraps

from telegram import Update, Document
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

import config
import claude_runner
import file_manager
import session_manager

logging.basicConfig(
    format="%(asctime)s %(levelname)s %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

BOT_START_TIME = time.time()

file_manager.set_upload_dir(config.UPLOAD_DIR)


def auth(func):
    """Decorator: silently ignores requests from non-allowed user IDs."""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_user and update.effective_user.id != config.ALLOWED_USER_ID:
            logger.warning("Blocked request from user_id=%s", update.effective_user.id)
            return
        return await func(update, context)
    return wrapper


async def send_long(update: Update, text: str, chunk_size: int = 4000) -> None:
    """Send text in chunks to stay within Telegram's 4096-char limit."""
    text = text.strip()
    if not text:
        return
    for i in range(0, len(text), chunk_size):
        chunk = text[i:i + chunk_size]
        await update.message.reply_text(f"```\n{chunk}\n```", parse_mode="Markdown")


@auth
async def cmd_new(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("Uso: /new <nome> [<diret\u00f3rio>]")
        return
    name = context.args[0]
    cwd = context.args[1] if len(context.args) > 1 else "~"
    if session_manager.new_session(name, cwd):
        expanded = session_manager.get_session_cwd(name)
        await update.message.reply_text(
            f"\u2713 Sess\u00e3o criada. Ativa: `{name}`\nDiret\u00f3rio: `{expanded}`",
            parse_mode="Markdown",
        )
    else:
        await update.message.reply_text(
            f"\u274c Sess\u00e3o `{name}` j\u00e1 existe. Use /attach para ativ\u00e1-la.",
            parse_mode="Markdown",
        )


@auth
async def cmd_attach(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("Uso: /attach <nome>")
        return
    name = context.args[0]
    if session_manager.attach_session(name):
        await update.message.reply_text(f"\u2713 Ativa: `{name}`", parse_mode="Markdown")
    else:
        await update.message.reply_text(
            f"\u274c Sess\u00e3o `{name}` n\u00e3o encontrada.", parse_mode="Markdown"
        )


@auth
async def cmd_sessions(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    sessions = session_manager.list_sessions()
    active = session_manager.get_active()
    if not sessions:
        await update.message.reply_text(
            "Nenhuma sess\u00e3o aberta. Use /new <nome> para criar."
        )
        return
    lines = []
    for s in sessions:
        marker = " \u2190 ativa" if s == active else ""
        cwd = session_manager.get_session_cwd(s)
        lines.append(f"\u2022 `{s}`{marker}\n  `{cwd}`")
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


@auth
async def cmd_kill(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("Uso: /kill <nome>")
        return
    name = context.args[0]
    if session_manager.kill_session(name):
        await update.message.reply_text(
            f"\u2713 Sess\u00e3o `{name}` encerrada.", parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            f"\u274c Sess\u00e3o `{name}` n\u00e3o encontrada.", parse_mode="Markdown"
        )


@auth
async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    active = session_manager.get_active()
    uptime = int(time.time() - BOT_START_TIME)
    hours, remainder = divmod(uptime, 3600)
    minutes = remainder // 60
    active_text = f"`{active}`" if active else "nenhuma"
    await update.message.reply_text(
        f"Sess\u00e3o ativa: {active_text}\nUptime: {hours}h {minutes}m",
        parse_mode="Markdown",
    )


@auth
async def cmd_send(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("Uso: /send <caminho>")
        return
    path_str = " ".join(context.args)
    path, error = file_manager.resolve_send_path(path_str)
    if error:
        await update.message.reply_text(error)
        return
    with open(path, "rb") as f:
        await update.message.reply_document(f)


@auth
async def cmd_ls(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    path = " ".join(context.args) if context.args else "~"
    result = file_manager.list_dir(path)
    text = f"\U0001f4c2 {path}\n\n{result}"
    for i in range(0, len(text), 4000):
        await update.message.reply_text(text[i:i + 4000])


@auth
async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    doc: Document = update.message.document
    dest = file_manager.upload_destination(doc.file_name)
    tg_file = await doc.get_file()
    await tg_file.download_to_drive(dest)
    await update.message.reply_text(f"\u2713 Salvo em: `{dest}`", parse_mode="Markdown")


@auth
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    active = session_manager.get_active()
    if not active:
        await update.message.reply_text(
            "Nenhuma sess\u00e3o ativa.\n"
            "Use /new <nome> para criar ou /attach <nome> para ativar."
        )
        return
    cwd = session_manager.get_session_cwd(active)
    claude_id = session_manager.get_claude_id(active)
    await update.message.reply_text("\u23f3 Processando...")
    response, new_id = claude_runner.run_claude(update.message.text, cwd, claude_id)
    if new_id:
        session_manager.set_claude_id(active, new_id)
    await send_long(update, response)


def main() -> None:
    app = Application.builder().token(config.BOT_TOKEN).build()

    app.add_handler(CommandHandler("new", cmd_new))
    app.add_handler(CommandHandler("attach", cmd_attach))
    app.add_handler(CommandHandler("sessions", cmd_sessions))
    app.add_handler(CommandHandler("kill", cmd_kill))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("send", cmd_send))
    app.add_handler(CommandHandler("ls", cmd_ls))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    logger.info("Bot iniciado. Polling...")
    app.run_polling()


if __name__ == "__main__":
    main()
