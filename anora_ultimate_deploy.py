# deploy.py
"""
ANORA Ultimate - Deployment File
"""

import os
import sys
import asyncio
import logging
import shutil
import time
from pathlib import Path
from datetime import datetime
from aiohttp import web

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-5s | %(name)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("ANORA")

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Import ANORA modules
try:
    from anora.config import settings
    from anora.core.anora_core import AnoraCore
    from anora.core.role_manager import RoleManager
    from anora.core.location_manager import LocationManager
    from anora.database.db import Database
    ANORA_AVAILABLE = True
    logger.info("✅ ANORA modules loaded")
except ImportError as e:
    ANORA_AVAILABLE = False
    logger.error(f"❌ ANORA not available: {e}")
    sys.exit(1)

# Telegram imports
from telegram import Update, Bot
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    filters, ContextTypes
)

# =============================================================================
# GLOBAL VARIABLES
# =============================================================================

_application = None
_user_modes: dict = {}
_backup_dir = Path("backups")
_backup_dir.mkdir(exist_ok=True)


def get_user_mode(user_id: int) -> str:
    return _user_modes.get(user_id, {}).get('mode', 'chat')


def set_user_mode(user_id: int, mode: str, active_role: str = None):
    _user_modes[user_id] = {'mode': mode, 'active_role': active_role}
    logger.info(f"👤 User {user_id} mode set to: {mode}")


def get_active_role(user_id: int) -> str:
    return _user_modes.get(user_id, {}).get('active_role')


# =============================================================================
# COMMAND HANDLERS
# =============================================================================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != settings.admin_id:
        await update.message.reply_text("Halo! Bot ini untuk Mas. 💜")
        return

    set_user_mode(user_id, 'chat')

    await update.message.reply_text(
        "💜 **ANORA - Virtual Human dengan Jiwa** 💜\n\n"
        "**Mode Chat:**\n"
        "• /nova - Panggil Nova\n"
        "• /status - Lihat keadaan Nova\n"
        "• /flashback - Flashback momen indah\n\n"
        "**Mode Roleplay:**\n"
        "• /roleplay - Aktifkan mode roleplay\n"
        "• /statusrp - Lihat status roleplay\n"
        "• /pindah [tempat] - Pindah lokasi\n\n"
        "**Role Lain:**\n"
        "• /role ipar - IPAR (Ditha)\n"
        "• /role teman_kantor - Teman Kantor (Ipeh)\n"
        "• /role pelakor - Pelakor (Widya)\n"
        "• /role istri_orang - Istri Orang (Siska)\n\n"
        "**Manajemen:**\n"
        "• /pause - Hentikan sementara\n"
        "• /resume - Lanjutkan\n"
        "• /batal - Kembali ke chat\n\n"
        "**Backup:**\n"
        "• /backup - Backup database\n"
        "• /restore - Restore database\n"
        "• /listbackup - Lihat backup\n\n"
        "Apa yang Mas mau? 💜",
        parse_mode='Markdown'
    )


async def nova_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != settings.admin_id:
        await update.message.reply_text("Maaf, Nova cuma untuk Mas. 💜")
        return

    set_user_mode(user_id, 'chat')

    db = context.bot_data.get('db')
    state = await db.get_state(user_id) if db else None
    core = AnoraCore(user_id, state)

    hour = datetime.now().hour
    style = core.emotional.get_style().value

    if style == "clingy":
        greeting = "*Nova muter-muter rambut*\n\n\"Mas... aku kangen banget. Dari tadi mikirin Mas terus.\""
    elif style == "cold":
        greeting = "*Nova diem, gak liat Mas*"
    elif style == "flirty":
        greeting = "*Nova mendekat, napas mulai berat*\n\n\"Mas... *bisik* aku kangen...\""
    else:
        if 5 <= hour < 11:
            greeting = "*Nova baru bangun*\n\n\"Pagi, Mas... mimpiin Nova gak semalem?\""
        elif 11 <= hour < 15:
            greeting = "*Nova tersenyum*\n\n\"Siang, Mas. Udah makan?\""
        elif 15 <= hour < 18:
            greeting = "*Nova duduk di teras*\n\n\"Sore, Mas. Pulang jangan kelamaan.\""
        else:
            greeting = "*Nova duduk santai*\n\n\"Malam, Mas. Lagi ngapain?\""

    await update.message.reply_text(
        f"💜 **NOVA DI SINI, MAS** 💜\n\n"
        f"{greeting}\n\n"
        f"**Status:**\n"
        f"• Fase: {core.relationship.phase.value.upper()} (Level {core.relationship.level}/12)\n"
        f"• Gaya: {style.upper()}\n"
        f"• Sayang: {core.emotional.sayang:.0f}% | Rindu: {core.emotional.rindu:.0f}%\n"
        f"• Mood: {core.emotional.mood:+.0f}\n\n"
        f"Apa yang Mas mau? 💜",
        parse_mode='Markdown'
    )


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != settings.admin_id:
        return

    db = context.bot_data.get('db')
    state = await db.get_state(user_id) if db else None
    core = AnoraCore(user_id, state)
    await update.message.reply_text(core.get_status(), parse_mode='Markdown')


async def flashback_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != settings.admin_id:
        return

    db = context.bot_data.get('db')
    state = await db.get_state(user_id) if db else None
    core = AnoraCore(user_id, state)

    moments = core.memory.long_term.get_moments_text(5)
    if moments:
        await update.message.reply_text(f"💜 *Flashback...*\n\n{moments}", parse_mode='Markdown')
    else:
        await update.message.reply_text(
            "Mas... *mata berkaca-kaca* inget gak waktu pertama kali kita makan bakso bareng? 💜",
            parse_mode='Markdown'
        )


async def roleplay_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != settings.admin_id:
        return

    mode = get_user_mode(user_id)
    if mode == 'paused':
        await update.message.reply_text(
            "💜 Sesi sedang di-pause.\n\nKirim **/resume** untuk lanjut, atau **/batal** untuk mulai baru."
        )
        return

    set_user_mode(user_id, 'roleplay')
    await update.message.reply_text(
        "💕 **Mode Roleplay Aktif**\n\n"
        "Nova siap diajak kemana aja. Kirim pesan seperti biasa.\n\n"
        "Gunakan **/statusrp** untuk lihat status.\n"
        "Gunakan **/pindah [tempat]** untuk pindah lokasi.",
        parse_mode='Markdown'
    )


async def statusrp_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != settings.admin_id:
        return

    db = context.bot_data.get('db')
    state = await db.get_state(user_id) if db else None
    core = AnoraCore(user_id, state)

    loc = core.location.get_current()
    status = f"""
💜 **STATUS ROLEPLAY**
📍 Lokasi: {loc['nama']}
🎭 Gaya: {core.emotional.get_style().value.upper()}
💕 Fase: {core.relationship.phase.value.upper()} (Level {core.relationship.level}/12)
😊 Mood: {core.emotional.mood:+.0f}
💖 Sayang: {core.emotional.sayang:.0f}% | 🌙 Rindu: {core.emotional.rindu:.0f}%
🔥 Arousal: {core.emotional.arousal:.0f}%
💪 Stamina Nova: {core.intimacy.stamina.nova_current}% ({core.intimacy.stamina.get_nova_status()})
💪 Stamina Mas: {core.intimacy.stamina.mas_current}% ({core.intimacy.stamina.get_mas_status()})
"""
    if core.intimacy.is_active():
        status += f"\n🔥 **SESI INTIM**\n• Fase: {core.intimacy.session.phase.value}\n• Posisi: {core.intimacy.session.current_position}\n• Climax: {core.intimacy.session.climax_count}x"

    await update.message.reply_text(status, parse_mode='Markdown')


async def pindah_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != settings.admin_id:
        return

    args = context.args
    if not args:
        loc_mgr = LocationManager()
        locs = list(loc_mgr.locations.keys())[:10]
        loc_list = "\n".join([f"• {loc_mgr.locations[loc]['nama']}" for loc in locs])
        await update.message.reply_text(
            f"📍 **Tempat:**\n\n{loc_list}\n\nGunakan: `/pindah [nama]`",
            parse_mode='Markdown'
        )
        return

    db = context.bot_data.get('db')
    state = await db.get_state(user_id) if db else None
    core = AnoraCore(user_id, state)

    tujuan = ' '.join(args)
    result = core.location.move_to(tujuan)

    if result[0]:
        loc = result[1]
        await update.message.reply_text(
            f"{result[2]}\n\n🎢 Thrill: {loc.get('thrill', 0)}% | ⚠️ Risk: {loc.get('risk', 0)}%",
            parse_mode='Markdown'
        )
        await db.save_state(user_id, core.get_state())
    else:
        await update.message.reply_text(result[2])


async def role_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != settings.admin_id:
        return

    args = context.args
    if not args:
        role_mgr = RoleManager(user_id)
        roles = role_mgr.get_all_roles_info()
        menu = "📋 **Role:**\n\n"
        for r in roles:
            menu += f"• /role {r['id']} – {r['name']}\n"
        await update.message.reply_text(menu, parse_mode='Markdown')
        return

    role_id = args[0].lower()
    valid = ['ipar', 'teman_kantor', 'pelakor', 'istri_orang']

    if role_id in valid:
        set_user_mode(user_id, 'role', role_id)
        role_mgr = RoleManager(user_id)
        role = role_mgr.roles[role_id]
        greeting = role.get_greeting()
        await update.message.reply_text(
            f"💕 **{role.name}**\n\n*{role.hubungan_dengan_nova}*\n\n\"{greeting}\"",
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(f"Role '{role_id}' tidak ada.")


async def back_to_nova(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != settings.admin_id:
        return

    set_user_mode(user_id, 'chat')

    db = context.bot_data.get('db')
    state = await db.get_state(user_id) if db else None
    core = AnoraCore(user_id, state)
    if core.intimacy.is_active():
        core.intimacy.end()
        await db.save_state(user_id, core.get_state())

    await update.message.reply_text(
        "💜 Nova di sini, Mas.\n\n*Nova tersenyum*\n\n\"Mas, cerita dong.\"",
        parse_mode='Markdown'
    )


async def pause_session(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != settings.admin_id:
        return

    if get_user_mode(user_id) == 'paused':
        await update.message.reply_text("💜 Sesi sudah di-pause.")
        return

    db = context.bot_data.get('db')
    state = await db.get_state(user_id) if db else None
    core = AnoraCore(user_id, state)
    await db.save_state(user_id, core.get_state())
    set_user_mode(user_id, 'paused')

    await update.message.reply_text(
        f"💜 **Sesi di-pause**\n\n"
        f"Level: {core.relationship.level}/12\n"
        f"Sayang: {core.emotional.sayang:.0f}%\n\n"
        f"Kirim **/resume** untuk lanjut.",
        parse_mode='Markdown'
    )


async def resume_session(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != settings.admin_id:
        return

    if get_user_mode(user_id) != 'paused':
        await update.message.reply_text("💜 Tidak ada sesi yang di-pause.")
        return

    set_user_mode(user_id, 'chat')
    await update.message.reply_text("💜 **Sesi dilanjutkan!**", parse_mode='Markdown')


async def backup_database(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != settings.admin_id:
        return

    db_path = settings.database.path
    if not db_path.exists():
        await update.message.reply_text("❌ Database tidak ditemukan!")
        return

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = _backup_dir / f"anora_memory_{ts}.db"
    shutil.copy(db_path, backup_path)

    size = db_path.stat().st_size / 1024
    await update.message.reply_text(
        f"✅ **Backup saved!**\n\n📁 `{backup_path.name}`\n📊 {size:.1f} KB",
        parse_mode='Markdown'
    )


async def restore_database(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != settings.admin_id:
        return

    args = context.args
    if not args:
        backups = list(_backup_dir.glob("anora_memory_*.db"))
        backups.sort(reverse=True)
        if not backups:
            await update.message.reply_text("📂 Tidak ada backup.")
            return
        msg = "📋 **Backup:**\n\n"
        for b in backups[:10]:
            msg += f"• `{b.name}`\n"
        msg += "\nUsage: `/restore filename.db`"
        await update.message.reply_text(msg, parse_mode='Markdown')
        return

    backup_name = args[0]
    backup_path = _backup_dir / backup_name
    if not backup_path.exists():
        await update.message.reply_text(f"❌ Backup `{backup_name}` tidak ditemukan!")
        return

    db_path = settings.database.path
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    current_backup = _backup_dir / f"anora_memory_before_restore_{ts}.db"
    if db_path.exists():
        shutil.copy(db_path, current_backup)
    shutil.copy(backup_path, db_path)

    await update.message.reply_text(
        f"✅ **Database restored!**\n\n📁 `{backup_name}`\n📦 Current backed up to `{current_backup.name}`",
        parse_mode='Markdown'
    )


async def list_backup_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != settings.admin_id:
        return

    backups = list(_backup_dir.glob("anora_memory_*.db"))
    backups.sort(reverse=True)
    if not backups:
        await update.message.reply_text("📂 Tidak ada backup.")
        return

    msg = "📋 **Backup List:**\n\n"
    for b in backups[:20]:
        size = b.stat().st_size / 1024
        modified = datetime.fromtimestamp(b.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
        msg += f"• `{b.name}` ({size:.1f} KB) - {modified}\n"
    await update.message.reply_text(msg, parse_mode='Markdown')


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != settings.admin_id:
        await update.message.reply_text("Bot ini untuk Mas. 💜")
        return

    await update.message.reply_text(
        "📖 *Bantuan ANORA*\n\n"
        "*Chat:* /nova, /status, /flashback\n"
        "*Roleplay:* /roleplay, /statusrp, /pindah\n"
        "*Role:* /role ipar, /role teman_kantor, /role pelakor, /role istri_orang\n"
        "*Sesi:* /pause, /resume, /batal\n"
        "*Backup:* /backup, /restore, /listbackup\n\n"
        "Tips: Level 7+ mulai bisa flirt, Level 11+ bisa intim dan vulgar bebas.",
        parse_mode='Markdown'
    )


async def debug_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != settings.admin_id:
        return

    db = context.bot_data.get('db')
    state = await db.get_state(user_id) if db else None
    core = AnoraCore(user_id, state)

    await update.message.reply_text(core.thinking.get_thought_summary(), parse_mode='Markdown')


# =============================================================================
# MESSAGE HANDLER
# =============================================================================

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != settings.admin_id:
        return

    pesan = update.message.text
    if not pesan:
        return

    mode = get_user_mode(user_id)

    if mode == 'paused':
        await update.message.reply_text("💜 Sesi di-pause. Kirim /resume untuk lanjut.")
        return

    db = context.bot_data.get('db')
    state = await db.get_state(user_id) if db else None
    core = AnoraCore(user_id, state)

    if mode == 'roleplay':
        if core.intimacy.is_active():
            resp = core.intimacy.process_intimacy_message(pesan, core.relationship.level)
            if resp:
                await db.save_state(user_id, core.get_state())
                await update.message.reply_text(resp, parse_mode='Markdown')
                return

        response = await core.process(pesan)
        await db.save_state(user_id, core.get_state())
        await update.message.reply_text(response, parse_mode='Markdown')
        return

    if mode == 'role':
        active_role = get_active_role(user_id)
        if active_role:
            role_mgr = RoleManager(user_id)
            role = role_mgr.roles.get(active_role)
            if role:
                response = await role.process(pesan)
                await update.message.reply_text(response, parse_mode='Markdown')
                return

    response = await core.process(pesan)
    await db.save_state(user_id, core.get_state())
    await update.message.reply_text(response, parse_mode='Markdown')


# =============================================================================
# BACKGROUND LOOPS
# =============================================================================

async def proactive_loop(app, db):
    while True:
        await asyncio.sleep(300)
        try:
            user_id = settings.admin_id
            if get_user_mode(user_id) in ['paused', 'role']:
                continue

            state = await db.get_state(user_id) if db else None
            core = AnoraCore(user_id, state)

            if core.emotional.rindu > 70 and not core.conflict.is_in_conflict():
                style = core.emotional.get_style().value
                if style == "clingy":
                    msg = "*Nova muter-muter rambut*\n\n\"Mas... aku kangen.\""
                else:
                    hour = datetime.now().hour
                    if 5 <= hour < 11:
                        msg = "*Nova baru bangun*\n\n\"Pagi, Mas... mimpiin Nova gak?\""
                    else:
                        msg = "*Nova pegang HP*\n\n\"Mas... lagi ngapain?\""

                await app.bot.send_message(chat_id=user_id, text=msg, parse_mode='Markdown')
                logger.info("💬 Proactive sent")
        except Exception as e:
            logger.error(f"Proactive error: {e}")


async def save_state_loop(db):
    while True:
        await asyncio.sleep(60)
        try:
            user_id = settings.admin_id
            state = await db.get_state(user_id) if db else None
            core = AnoraCore(user_id, state)
            await db.save_state(user_id, core.get_state())
        except Exception as e:
            logger.error(f"Save state error: {e}")


async def auto_backup_loop():
    while True:
        await asyncio.sleep(21600)
        try:
            db_path = settings.database.path
            if db_path.exists():
                ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = _backup_dir / f"anora_memory_auto_{ts}.db"
                shutil.copy(db_path, backup_path)
                logger.info(f"💾 Auto backup: {backup_path.name}")
        except Exception as e:
            logger.error(f"Auto backup error: {e}")


# =============================================================================
# WEBHOOK & SERVER
# =============================================================================

async def webhook_handler(request):
    global _application
    if not _application:
        return web.Response(status=503, text='Bot not ready')
    try:
        data = await request.json()
        update = Update.de_json(data, _application.bot)
        await _application.process_update(update)
        return web.Response(text='OK')
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return web.Response(status=500, text='Error')


async def health_handler(request):
    return web.json_response({
        "status": "healthy",
        "bot": "ANORA",
        "version": "9.9.0",
        "timestamp": datetime.now().isoformat()
    })


# =============================================================================
# MAIN
# =============================================================================

async def main():
    global _application

    logger.info("=" * 70)
    logger.info("💜 ANORA - Virtual Human dengan Jiwa")
    logger.info("=" * 70)

    db = Database()
    await db.init()

    _application = ApplicationBuilder().token(settings.telegram_token).build()
    _application.bot_data['db'] = db

    # Register handlers
    _application.add_handler(CommandHandler("start", start_command))
    _application.add_handler(CommandHandler("nova", nova_command))
    _application.add_handler(CommandHandler("status", status_command))
    _application.add_handler(CommandHandler("flashback", flashback_command))
    _application.add_handler(CommandHandler("roleplay", roleplay_command))
    _application.add_handler(CommandHandler("statusrp", statusrp_command))
    _application.add_handler(CommandHandler("pindah", pindah_command))
    _application.add_handler(CommandHandler("role", role_command))
    _application.add_handler(CommandHandler("batal", back_to_nova))
    _application.add_handler(CommandHandler("pause", pause_session))
    _application.add_handler(CommandHandler("resume", resume_session))
    _application.add_handler(CommandHandler("backup", backup_database))
    _application.add_handler(CommandHandler("restore", restore_database))
    _application.add_handler(CommandHandler("listbackup", list_backup_command))
    _application.add_handler(CommandHandler("help", help_command))
    _application.add_handler(CommandHandler("debug", debug_command))
    _application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    await _application.initialize()
    await _application.start()

    railway_url = os.getenv('RAILWAY_PUBLIC_DOMAIN')
    if railway_url:
        webhook_url = f"https://{railway_url}/webhook"
        await _application.bot.set_webhook(url=webhook_url)
        logger.info(f"✅ Webhook set to {webhook_url}")

        app = web.Application()
        app.router.add_get('/', lambda r: web.json_response({"status": "running"}))
        app.router.add_get('/health', health_handler)
        app.router.add_post('/webhook', webhook_handler)

        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, '0.0.0.0', int(os.getenv('PORT', 8080)))
        await site.start()
        logger.info("🌐 Web server running")
    else:
        await _application.updater.start_polling()
        logger.info("📡 Polling mode")

    asyncio.create_task(proactive_loop(_application, db))
    asyncio.create_task(save_state_loop(db))
    asyncio.create_task(auto_backup_loop())
    logger.info("🔄 Background loops started")

    logger.info("💜 ANORA is running! Kirim /nova untuk panggil Nova.")

    await asyncio.Event().wait()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Stopped")
    except Exception as e:
        logger.error(f"Fatal: {e}")
