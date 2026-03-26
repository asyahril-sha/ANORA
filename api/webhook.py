# app/api/webhook.py
"""
Webhook endpoint – menerima update Telegram dan meneruskan ke core atau command handler.
"""

import logging
from fastapi import APIRouter, Request, HTTPException
from telegram import Update, Bot

from ..database.db import Database
from ..core.anora_core import AnoraCore
from ..api.commands import handle_command
from ..config import settings

logger = logging.getLogger(__name__)

router = APIRouter()
_bot: Bot = None


def set_bot(bot: Bot):
    global _bot
    _bot = bot


@router.post(settings.webhook.path)
async def webhook(request: Request):
    if not _bot:
        raise HTTPException(status_code=503, detail="Bot not ready")

    data = await request.json()
    update = Update.de_json(data, _bot)
    if not update.message or not update.message.text:
        return {"ok": True}

    user_id = update.effective_user.id
    text = update.message.text

    db: Database = request.app.state.db
    user_state = await db.get_state(user_id) or {}

    # Handle command
    if text.startswith('/'):
        parts = text.split()
        cmd = parts[0].lower()
        args = parts[1:]
        handled = await handle_command(cmd, args, user_id, db, _bot, user_state)
        if handled:
            return {"ok": True}
        # jika command tidak dikenali, abaikan

    # Normal message processing
    mode = user_state.get('mode', 'chat')
    active_role = user_state.get('active_role')

    if mode == 'role' and active_role:
        # Gunakan role manager
        from ..core.role_manager import RoleManager
        role_mgr = RoleManager(user_id)
        # load state role
        role_state = user_state.get('role_states', {})
        role_mgr.load_state(role_state)
        role = role_mgr.get_active()
        if role:
            response = await role.process(text)
            # save state
            user_state['role_states'] = role_mgr.get_state()
            await db.save_state(user_id, user_state)
            await _bot.send_message(chat_id=user_id, text=response, parse_mode="Markdown")
        else:
            # fallback ke core
            core = AnoraCore(user_id, user_state.get('core'))
            response = await core.process(text)
            user_state['core'] = core.get_state()
            await db.save_state(user_id, user_state)
            await _bot.send_message(chat_id=user_id, text=response, parse_mode="Markdown")
    else:
        core = AnoraCore(user_id, user_state.get('core'))
        response = await core.process(text)
        user_state['core'] = core.get_state()
        await db.save_state(user_id, user_state)
        await _bot.send_message(chat_id=user_id, text=response, parse_mode="Markdown")

    return {"ok": True}
