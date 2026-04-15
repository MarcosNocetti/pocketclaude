import asyncio
import json
import logging
import os
import time
from functools import wraps
from datetime import datetime

from telegram import Update, Document
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

import config
import auth_manager
import claude_runner
import file_manager
import session_manager
import queue_manager

logging.basicConfig(
    format="%(asctime)s %(levelname)s %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)
DEBUG_FLOW_FILE = os.path.join(os.path.dirname(__file__), "bot_flow_debug.log")

BOT_START_TIME = time.time()

file_manager.set_upload_dir(config.UPLOAD_DIR)


def flow_debug(event: str, **payload) -> None:
    try:
        with open(DEBUG_FLOW_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps({
                "ts": datetime.now().isoformat(),
                "event": event,
                **payload,
            }, ensure_ascii=False) + "\n")
    except OSError:
        pass


def auth(func):
    """Decorator: blocks unknown user IDs and unauthenticated (2FA) sessions."""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        flow_debug(
            "auth_check",
            handler=func.__name__,
            user_id=update.effective_user.id if update.effective_user else None,
            text=update.message.text if update.message else None,
            authenticated=auth_manager.is_authenticated(),
            active_session=session_manager.get_active(),
        )
        logger.info(
            "auth_check handler=%s user_id=%s text=%r authenticated=%s active_session=%s",
            func.__name__,
            update.effective_user.id if update.effective_user else None,
            update.message.text if update.message else None,
            auth_manager.is_authenticated(),
            session_manager.get_active(),
        )
        if update.effective_user and update.effective_user.id != config.ALLOWED_USER_ID:
            logger.warning("Blocked request from user_id=%s", update.effective_user.id)
            return
        if not auth_manager.is_authenticated():
            await update.message.reply_text(
                "🔒 Sessão expirada ou não autenticada.\nUse `/login <código>`",
                parse_mode="Markdown",
            )
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


async def _dispatch_queue(context: ContextTypes.DEFAULT_TYPE) -> None:
    """JobQueue callback: send all queued messages to Claude when limit resets."""
    messages = queue_manager.pop_all()
    flow_debug("dispatch_queue_start", message_count=len(messages))
    if not messages:
        return
    chat_id = context.job.data["chat_id"]
    await context.bot.send_message(
        chat_id=chat_id,
        text=f"\u23f0 Limite resetado \u2014 disparando {len(messages)} mensagem(ns) da fila...",
    )
    for entry in messages:
        session_name = entry["session_name"]
        cwd = entry["cwd"]
        claude_id = entry["claude_id"]
        text = entry["text"]

        await context.bot.send_message(
            chat_id=chat_id,
            text=f"\U0001f4e4 Enviando para `{session_name}`:\n_{text[:200]}_",
            parse_mode="Markdown",
        )
        response, new_id = await asyncio.to_thread(claude_runner.run_claude, text, cwd, claude_id)
        flow_debug(
            "dispatch_queue_response",
            session_name=session_name,
            rate_limited=queue_manager.is_rate_limited(response),
            response_preview=response[:300],
            new_id=new_id,
        )
        logger.info(
            "dispatch_queue session=%s rate_limited=%s response_preview=%r",
            session_name,
            queue_manager.is_rate_limited(response),
            response[:300],
        )
        if new_id:
            session_manager.set_claude_id(session_name, new_id)

        if queue_manager.is_rate_limited(response):
            reset_at = queue_manager.parse_reset_time(response)
            queue_manager.enqueue(
                chat_id=chat_id,
                session_name=session_name,
                cwd=cwd,
                claude_id=new_id or claude_id,
                text=text,
                reset_at=reset_at,
            )
            flow_debug(
                "dispatch_queue_reenqueued",
                session_name=session_name,
                reset_at=reset_at.isoformat() if reset_at else None,
            )
            if reset_at:
                context.job_queue.run_once(
                    _dispatch_queue,
                    when=reset_at,
                    name="dispatch_queue",
                    data={"chat_id": chat_id},
                )
            reset_str = reset_at.strftime("%H:%M") if reset_at else "horário desconhecido"
            await context.bot.send_message(
                chat_id=chat_id,
                text=(
                    "⚠️ Claude ainda sem créditos.\n"
                    f"✉️ Mensagem reenfileirada para {reset_str} (BRT)."
                ),
            )
            continue

        response = response.strip()
        for i in range(0, max(len(response), 1), 4000):
            chunk = response[i:i + 4000]
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"```\n{chunk}\n```",
                parse_mode="Markdown",
            )


async def _forward_to_claude(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str) -> None:
    """Forward text to the active Claude session."""
    active = session_manager.get_active()
    flow_debug("forward_start", active_session=active, text=text)
    if not active:
        await update.message.reply_text(
            "Nenhuma sess\u00e3o ativa.\n"
            "Use /new <nome> para criar ou /attach <nome> para ativar."
        )
        return
    cwd = session_manager.get_session_cwd(active)
    claude_id = session_manager.get_claude_id(active)
    status_msg = await update.message.reply_text("\u23f3 Processando...")

    async def _heartbeat(msg):
        elapsed = 0
        while True:
            await asyncio.sleep(30)
            elapsed += 30
            try:
                await msg.edit_text(f"\u23f3 Processando... ({elapsed}s)")
            except Exception:
                pass

    heartbeat = asyncio.create_task(_heartbeat(status_msg))
    try:
        response, new_id = await asyncio.to_thread(claude_runner.run_claude, text, cwd, claude_id)
    finally:
        heartbeat.cancel()
    try:
        await status_msg.delete()
    except Exception:
        pass
    flow_debug(
        "forward_response",
        active_session=active,
        rate_limited=queue_manager.is_rate_limited(response),
        response_preview=response[:300],
        old_id=claude_id,
        new_id=new_id,
    )
    logger.info(
        "forward_to_claude session=%s rate_limited=%s response_preview=%r",
        active,
        queue_manager.is_rate_limited(response),
        response[:300],
    )
    if new_id:
        session_manager.set_claude_id(active, new_id)

    # Detect rate limit — enqueue and schedule dispatch
    if queue_manager.is_rate_limited(response):
        reset_at = queue_manager.parse_reset_time(response)
        chat_id = update.effective_chat.id
        count = queue_manager.enqueue(
            chat_id=chat_id,
            session_name=active,
            cwd=cwd,
            claude_id=new_id or claude_id,
            text=text,
            reset_at=reset_at,
        )
        flow_debug(
            "forward_enqueued",
            active_session=active,
            count=count,
            reset_at=reset_at.isoformat() if reset_at else None,
        )
        # Only schedule one job — it pops everything when it fires
        existing = [j for j in context.job_queue.jobs() if j.name == "dispatch_queue"]
        if not existing and reset_at:
            context.job_queue.run_once(
                _dispatch_queue,
                when=reset_at,
                name="dispatch_queue",
                data={"chat_id": chat_id},
            )
        reset_str = reset_at.strftime("%H:%M") if reset_at else "hor\u00e1rio desconhecido"
        await update.message.reply_text(
            f"\u26a0\ufe0f Claude sem cr\u00e9ditos.\n"
            f"\u2709\ufe0f Mensagem #{count} enfileirada \u2014 ser\u00e1 enviada \u00e0s {reset_str} (BRT).",
        )
        return

    await send_long(update, response)


@auth
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = update.message.text
    logger.info("handle_text received text=%r", text)
    # "//" prefix: escape para enviar slash-commands do Claude Code que conflitam
    # com comandos do bot (ex: "//login" envia "/login" ao Claude)
    if text.startswith("//"):
        text = text[1:]
    await _forward_to_claude(update, context, text)


@auth
async def handle_unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Repassa comandos desconhecidos ao Claude (ex: /usage, /help, /clear)."""
    logger.info("handle_unknown_command received text=%r", update.message.text)
    await _forward_to_claude(update, context, update.message.text)


@auth
async def cmd_messages(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """List queued messages."""
    messages = queue_manager.list_messages()
    if not messages:
        await update.message.reply_text("\U0001f4ed Fila vazia.")
        return
    lines = [f"*Fila de mensagens ({len(messages)}):*"]
    for i, entry in enumerate(messages, 1):
        preview = entry["text"][:80].replace("*", "").replace("`", "")
        session = entry["session_name"]
        reset_at = entry.get("reset_at", "")
        reset_str = reset_at[11:16] if reset_at else "?"
        lines.append(f"{i}. `{session}` \u2014 {reset_str} BRT\n   _{preview}_")
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


@auth
async def cmd_rmq(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Remove a message from the queue: /rmq <n> or /rmq all."""
    if not context.args:
        await update.message.reply_text("Uso: `/rmq <n>` ou `/rmq all`", parse_mode="Markdown")
        return
    arg = context.args[0].strip().lower()
    if arg == "all":
        count = queue_manager.clear()
        await update.message.reply_text(f"\U0001f5d1 {count} mensagem(ns) removida(s) da fila.")
    else:
        try:
            idx = int(arg)
        except ValueError:
            await update.message.reply_text("Uso: `/rmq <n>` ou `/rmq all`", parse_mode="Markdown")
            return
        if queue_manager.remove_message(idx):
            await update.message.reply_text(f"\u2713 Mensagem #{idx} removida.")
        else:
            await update.message.reply_text(f"\u274c \u00cdndice inv\u00e1lido.")


async def cmd_login(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """2FA login — only valid for ALLOWED_USER_ID."""
    if update.effective_user and update.effective_user.id != config.ALLOWED_USER_ID:
        logger.warning("Login attempt from unknown user_id=%s", update.effective_user.id)
        return
    if not context.args:
        await update.message.reply_text("Uso: `/login <código TOTP>`", parse_mode="Markdown")
        return
    code = context.args[0].strip()
    if auth_manager.verify_and_login(code):
        await update.message.reply_text(
            f"✅ Autenticado. Sessão válida por {auth_manager.remaining()}.",
        )
        logger.info("User %s authenticated via TOTP", update.effective_user.id)
    else:
        await update.message.reply_text("❌ Código inválido ou expirado.")
        logger.warning("Failed TOTP attempt from user_id=%s", update.effective_user.id)


@auth
async def cmd_logout(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    auth_manager.logout()
    await update.message.reply_text("🔒 Sessão encerrada.")


def main() -> None:
    app = Application.builder().token(config.BOT_TOKEN).build()

    app.add_handler(CommandHandler("login", cmd_login))
    app.add_handler(CommandHandler("logout", cmd_logout))
    app.add_handler(CommandHandler("new", cmd_new))
    app.add_handler(CommandHandler("attach", cmd_attach))
    app.add_handler(CommandHandler("sessions", cmd_sessions))
    app.add_handler(CommandHandler("kill", cmd_kill))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("send", cmd_send))
    app.add_handler(CommandHandler("ls", cmd_ls))
    app.add_handler(CommandHandler("messages", cmd_messages))
    app.add_handler(CommandHandler("rmq", cmd_rmq))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    # Fallback: comandos não reconhecidos pelo bot vão para o Claude
    app.add_handler(MessageHandler(filters.COMMAND, handle_unknown_command))

    logger.info("Bot iniciado. Polling...")
    app.run_polling()


if __name__ == "__main__":
    main()
