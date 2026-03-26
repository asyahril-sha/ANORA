# app/api/commands.py
"""
Handlers untuk command Telegram.
"""

import logging
from typing import Dict, Any

from ..core.anora_core import AnoraCore
from ..core.role_manager import RoleManager
from ..config import settings

logger = logging.getLogger(__name__)


async def handle_command(cmd: str, args: list, user_id: int, db, bot, user_state: Dict) -> bool:
    """
    Handle command, return True jika command ditangani.
    """
    if cmd == '/start':
        await bot.send_message(chat_id=user_id, text="Halo Mas, aku Nova. Kirim /nova untuk mulai ngobrol.")
        return True

    elif cmd == '/nova':
        user_state['mode'] = 'chat'
        user_state['active_role'] = None
        await db.save_state(user_id, user_state)
        await bot.send_message(chat_id=user_id, text="💜 Nova di sini, Mas. Kirim pesan apa aja.", parse_mode="Markdown")
        return True

    elif cmd == '/role':
        if not args:
            role_mgr = RoleManager(user_id)
            info = role_mgr.get_all_roles_info()
            msg = "📋 **Role yang tersedia:**\n"
            for r in info:
                msg += f"• /role {r['id']} – **{r['name']}** (Level {r['level']})\n"
            await bot.send_message(chat_id=user_id, text=msg, parse_mode="Markdown")
            return True
        role_id = args[0].lower()
        valid = ['ipar', 'teman_kantor', 'pelakor', 'istri_orang']
        if role_id in valid:
            user_state['mode'] = 'role'
            user_state['active_role'] = role_id
            await db.save_state(user_id, user_state)
            role_mgr = RoleManager(user_id)
            role = role_mgr.roles[role_id]
            greeting = getattr(role, 'get_greeting', lambda: f"Halo, {role.panggilan}.")()
            response = f"💕 **{role.name}** ({role_id.upper()})\n\n*{role.hubungan_dengan_nova}*\n\n\"{greeting}\""
            await bot.send_message(chat_id=user_id, text=response, parse_mode="Markdown")
        else:
            await bot.send_message(chat_id=user_id, text=f"Role '{role_id}' tidak dikenal.")
        return True

    elif cmd == '/pindah':
        if not args:
            await bot.send_message(chat_id=user_id, text="Gunakan: /pindah ke [nama lokasi]")
            return True
        loc_name = ' '.join(args)
        core = AnoraCore(user_id, user_state.get('core'))
        result = core.location.move_to(loc_name)
        if result[0]:
            await bot.send_message(chat_id=user_id, text=result[2], parse_mode="Markdown")
            user_state['core'] = core.get_state()
            await db.save_state(user_id, user_state)
        else:
            await bot.send_message(chat_id=user_id, text=result[2])
        return True

    elif cmd == '/status':
        core = AnoraCore(user_id, user_state.get('core'))
        status = core.get_status()
        await bot.send_message(chat_id=user_id, text=status, parse_mode="Markdown")
        return True

    elif cmd == '/batal':
        user_state['mode'] = 'chat'
        user_state['active_role'] = None
        await db.save_state(user_id, user_state)
        await bot.send_message(chat_id=user_id, text="💜 Kembali ke mode chat dengan Nova.", parse_mode="Markdown")
        return True

    elif cmd == '/debug' and user_id == settings.admin_id:
        core = AnoraCore(user_id, user_state.get('core'))
        thought_summary = core.thinking.get_thought_summary()
        await bot.send_message(chat_id=user_id, text=thought_summary, parse_mode="Markdown")
        return True

    # fallback
    return False
