# anora_ultimate_deploy.py
"""
=============================================================================
ANORA ULTIMATE - Virtual Human dengan Jiwa
Deployment file for AMORIA + ANORA Ultimate
=============================================================================
"""

import os
import sys
import asyncio
import json
import logging
import shutil
import time
from pathlib import Path
from typing import Dict, Optional, Any
from datetime import datetime
from aiohttp import web

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-5s | %(name)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("ANORA_ULTIMATE")

sys.path.insert(0, str(Path(__file__).parent))

# Import configuration from ANORA Ultimate
try:
    from anora_ultimate.config import settings
    from anora_ultimate.core.anora_core import AnoraCore
    from anora_ultimate.core.role_manager import RoleManager
    from anora_ultimate.core.thinking_engine import ThinkingEngine
    from anora_ultimate.core.location_manager import LocationManager
    from anora_ultimate.intimacy.flow import IntimacyFlow
    from anora_ultimate.database.db import Database
    from anora_ultimate.workers.background import start_worker
    ANORA_ULTIMATE_AVAILABLE = True
    logger.info("✅ ANORA Ultimate modules loaded")
except ImportError as e:
    ANORA_ULTIMATE_AVAILABLE = False
    logger.error(f"❌ ANORA Ultimate not available: {e}")
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
_user_modes: Dict[int, Dict] = {}  # user_id -> {'mode': 'chat'/'roleplay'/'role'/'paused', 'active_role': None}
_backup_dir = Path("backups")
_backup_dir.mkdir(exist_ok=True)


def get_user_mode(user_id: int) -> str:
    return _user_modes.get(user_id, {}).get('mode', 'chat')


def set_user_mode(user_id: int, mode: str, active_role: Optional[str] = None):
    _user_modes[user_id] = {'mode': mode, 'active_role': active_role}
    logger.info(f"👤 User {user_id} mode set to: {mode}")


def get_active_role(user_id: int) -> Optional[str]:
    return _user_modes.get(user_id, {}).get('active_role')


# =============================================================================
# COMMAND HANDLERS
# =============================================================================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler /start"""
    user_id = update.effective_user.id
    if user_id != settings.admin_id:
        await update.message.reply_text("Halo! Bot ini untuk Mas. 💜")
        return

    set_user_mode(user_id, 'chat')

    await update.message.reply_text(
        "💜 **ANORA ULTIMATE - Virtual Human dengan Jiwa** 💜\n\n"
        "**Mode Chat (ngobrol biasa):**\n"
        "• /nova - Panggil Nova\n"
        "• /status - Lihat keadaan Nova\n"
        "• /flashback - Flashback ke momen indah\n\n"
        "**Mode Roleplay (beneran ketemu):**\n"
        "• /roleplay - Aktifkan mode roleplay\n"
        "• /statusrp - Lihat status roleplay lengkap\n"
        "• /pindah [tempat] - Pindah lokasi\n\n"
        "**Tempat yang bisa dikunjungi:**\n"
        "• kost, apartemen, mobil, pantai, hutan, toilet mall\n"
        "• bioskop, taman, parkiran, tangga darurat, kantor malam, ruang rapat kaca\n\n"
        "**Role Lain (Mereka TAU Mas punya Nova):**\n"
        "• /role ipar - IPAR (Ditha)\n"
        "• /role teman_kantor - Teman Kantor (Ipeh)\n"
        "• /role pelakor - Pelakor (Widya)\n"
        "• /role istri_orang - Istri Orang (Siska)\n\n"
        "**Manajemen Sesi:**\n"
        "• /pause - Hentikan sesi sementara (memory tetap)\n"
        "• /resume - Lanjutkan sesi\n"
        "• /batal - Kembali ke mode chat\n\n"
        "**Backup & Restore:**\n"
        "• /backup - Backup database ANORA\n"
        "• /restore [filename] - Restore database\n"
        "• /listbackup - Lihat daftar backup\n\n"
        "Apa yang Mas mau? 💜",
        parse_mode='Markdown'
    )


async def nova_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler /nova"""
    user_id = update.effective_user.id
    if user_id != settings.admin_id:
        await update.message.reply_text("Maaf, Nova cuma untuk Mas. 💜")
        return

    set_user_mode(user_id, 'chat')

    # Load core from DB
    db = context.bot_data.get('db')
    state = await db.get_state(user_id) if db else None
    core = AnoraCore(user_id, state)

    # Get greeting based on time and emotional style
    hour = datetime.now().hour
    style = core.emotional.get_style().value

    if style == "clingy":
        greeting = "*Nova muter-muter rambut, duduk deket Mas*\n\n\"Mas... aku kangen banget. Dari tadi mikirin Mas terus.\""
    elif style == "cold":
        greeting = "*Nova diem, gak liat Mas*"
    elif style == "flirty":
        greeting = "*Nova mendekat, napas mulai berat*\n\n\"Mas... *bisik* aku kangen...\""
    else:
        if 5 <= hour < 11:
            greeting = "*Nova baru bangun, mata masih berat*\n\n\"Pagi, Mas... mimpiin Nova gak semalem?\""
        elif 11 <= hour < 15:
            greeting = "*Nova tersenyum manis*\n\n\"Siang, Mas. Udah makan?\""
        elif 15 <= hour < 18:
            greeting = "*Nova liat jam, duduk di teras*\n\n\"Sore, Mas. Pulang jangan kelamaan.\""
        else:
            greeting = "*Nova duduk santai, pegang HP*\n\n\"Malam, Mas. Lagi ngapain?\""

    await update.message.reply_text(
        f"💜 **NOVA DI SINI, MAS** 💜\n\n"
        f"{greeting}\n\n"
        f"**Status:**\n"
        f"• Fase: {core.relationship.phase.value.upper()} (Level {core.relationship.level}/12)\n"
        f"• Gaya: {style.upper()}\n"
        f"• Sayang: {core.emotional.sayang:.0f}% | Rindu: {core.emotional.rindu:.0f}%\n"
        f"• Mood: {core.emotional.mood:+.0f}\n\n"
        f"Mas bisa:\n"
        f"• /status - liat keadaan Nova lengkap\n"
        f"• /flashback - inget momen indah\n"
        f"• /roleplay - kalo mau kayak beneran ketemu\n\n"
        f"Apa yang Mas mau? 💜",
        parse_mode='Markdown'
    )


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler /status"""
    user_id = update.effective_user.id
    if user_id != settings.admin_id:
        return

    db = context.bot_data.get('db')
    state = await db.get_state(user_id) if db else None
    core = AnoraCore(user_id, state)
    status_text = core.get_status()
    await update.message.reply_text(status_text, parse_mode='Markdown')


async def flashback_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler /flashback"""
    user_id = update.effective_user.id
    if user_id != settings.admin_id:
        return

    db = context.bot_data.get('db')
    state = await db.get_state(user_id) if db else None
    core = AnoraCore(user_id, state)

    # Get recent moments from memory
    moments = core.memory.long_term.get_moments_text(5)
    if moments:
        await update.message.reply_text(
            f"💜 *Flashback...*\n\n{moments}",
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            "Mas... *mata berkaca-kaca* inget gak waktu pertama kali kita makan bakso bareng? Aku masih inget senyum Mas. 💜",
            parse_mode='Markdown'
        )


async def roleplay_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler /roleplay"""
    user_id = update.effective_user.id
    if user_id != settings.admin_id:
        return

    mode = get_user_mode(user_id)
    if mode == 'paused':
        await update.message.reply_text(
            "💜 **Sesi sedang di-pause** 💜\n\n"
            "Nova masih ingat semua yang sudah terjadi.\n"
            "Kirim **/resume** untuk lanjut, atau **/batal** untuk mulai baru."
        )
        return

    set_user_mode(user_id, 'roleplay')

    db = context.bot_data.get('db')
    state = await db.get_state(user_id) if db else None
    core = AnoraCore(user_id, state)

    # Start intimacy session if level >= 11
    if core.relationship.level >= 11:
        core.intimacy.start()
        intro = core.intimacy.get_status()
        await update.message.reply_text(
            f"💕 **Mode Roleplay Aktif**\n\n{intro}\n\n"
            "Mas bisa mulai intim kapan saja. Kirim pesan seperti biasa, Nova akan merespon sesuai situasi.\n\n"
            "Gunakan **/statusrp** untuk lihat status roleplay.",
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            "💕 **Mode Roleplay Aktif**\n\n"
            "Nova siap diajak kemana aja. Kirim pesan seperti biasa, Nova akan merespon sesuai situasi.\n\n"
            "Gunakan **/statusrp** untuk lihat status lengkap.\n"
            "Gunakan **/pindah [tempat]** untuk pindah lokasi.",
            parse_mode='Markdown'
        )


async def statusrp_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler /statusrp"""
    user_id = update.effective_user.id
    if user_id != settings.admin_id:
        return

    db = context.bot_data.get('db')
    state = await db.get_state(user_id) if db else None
    core = AnoraCore(user_id, state)

    status = f"""
💜 **STATUS ROLEPLAY**
📍 Lokasi: {core.location.get_current()['nama']}
🎭 Gaya: {core.emotional.get_style().value.upper()}
💕 Fase: {core.relationship.phase.value.upper()} (Level {core.relationship.level}/12)
😊 Mood: {core.emotional.mood:+.0f}
💖 Sayang: {core.emotional.sayang:.0f}% | 🌙 Rindu: {core.emotional.rindu:.0f}%
🔥 Arousal: {core.emotional.arousal:.0f}%
⚡ Tension: {core.intimacy.arousal.tension:.0f}
💪 Stamina Nova: {core.intimacy.stamina.get_nova_bar()} {core.intimacy.stamina.nova_current}% ({core.intimacy.stamina.get_nova_status()})
💪 Stamina Mas: {core.intimacy.stamina.get_mas_bar()} {core.intimacy.stamina.mas_current}% ({core.intimacy.stamina.get_mas_status()})
💦 Climax hari ini: {core.intimacy.stamina.climax_today}x
"""
    if core.intimacy.is_active():
        status += f"\n🔥 **SESI INTIM AKTIF**\n• Fase: {core.intimacy.session.phase.value}\n• Posisi: {core.intimacy.session.current_position}\n• Climax: {core.intimacy.session.climax_count}x"

    await update.message.reply_text(status, parse_mode='Markdown')


async def pindah_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler /pindah [tempat]"""
    user_id = update.effective_user.id
    if user_id != settings.admin_id:
        return

    args = context.args
    if not args:
        loc_mgr = LocationManager()
        # List locations
        locations = list(loc_mgr.locations.keys())[:10]
        loc_list = "\n".join([f"• {loc_mgr.locations[loc]['nama']}" for loc in locations])
        await update.message.reply_text(
            f"📍 **Tempat yang bisa dikunjungi:**\n\n{loc_list}\n\nGunakan: `/pindah [nama tempat]`",
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
            f"{result[2]}\n\n"
            f"🎢 Thrill: {loc.get('thrill', 0)}% | ⚠️ Risk: {loc.get('risk', 0)}%\n"
            f"💡 {loc.get('tips', '')}",
            parse_mode='Markdown'
        )
        # Save updated state
        await db.save_state(user_id, core.get_state())
    else:
        await update.message.reply_text(result[2], parse_mode='Markdown')


async def role_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler /role [nama]"""
    user_id = update.effective_user.id
    if user_id != settings.admin_id:
        return

    args = context.args
    if not args:
        role_mgr = RoleManager(user_id)
        roles = role_mgr.get_all_roles_info()
        menu = "📋 **Role yang tersedia:**\n\n"
        for r in roles:
            menu += f"• /role {r['id']} – **{r['name']}** (Level {r['level']})\n"
        menu += "\n_Ketik /nova kalo mau balik ke Nova._"
        await update.message.reply_text(menu, parse_mode='Markdown')
        return

    role_id = args[0].lower()
    valid_roles = ['ipar', 'teman_kantor', 'pelakor', 'istri_orang']

    if role_id in valid_roles:
        set_user_mode(user_id, 'role', role_id)
        role_mgr = RoleManager(user_id)
        role = role_mgr.roles[role_id]
        greeting = role.get_greeting()
        response = f"💕 **{role.name}** ({role_id.upper()})\n\n*{role.hubungan_dengan_nova}*\n\n\"{greeting}\""
        await update.message.reply_text(response, parse_mode='Markdown')
    else:
        await update.message.reply_text(
            f"Role '{role_id}' gak ada, Mas.\n\nPilih: ipar, teman_kantor, pelakor, istri_orang",
            parse_mode='Markdown'
        )


async def back_to_nova(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler /batal - Kembali ke mode chat"""
    user_id = update.effective_user.id
    if user_id != settings.admin_id:
        return

    set_user_mode(user_id, 'chat')

    # End intimacy session if active
    db = context.bot_data.get('db')
    state = await db.get_state(user_id) if db else None
    core = AnoraCore(user_id, state)
    if core.intimacy.is_active():
        core.intimacy.end()
        await db.save_state(user_id, core.get_state())

    await update.message.reply_text(
        "💜 Nova di sini, Mas.\n\n*Nova tersenyum*\n\n\"Mas, cerita dong tentang hari Mas.\"",
        parse_mode='Markdown'
    )


async def pause_session(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler /pause - Hentikan sesi sementara, memory tetap tersimpan"""
    user_id = update.effective_user.id
    if user_id != settings.admin_id:
        return

    mode = get_user_mode(user_id)
    if mode == 'paused':
        await update.message.reply_text("💜 Sesi sudah dalam keadaan pause.")
        return

    # Save state before pause
    db = context.bot_data.get('db')
    state = await db.get_state(user_id) if db else None
    core = AnoraCore(user_id, state)
    await db.save_state(user_id, core.get_state())

    set_user_mode(user_id, 'paused')

    await update.message.reply_text(
        f"💜 **Sesi dihentikan sementara** 💜\n\n"
        f"Nova akan tetap ingat semua yang sudah terjadi:\n"
        f"• Level: {core.relationship.level}/12\n"
        f"• Sayang: {core.emotional.sayang:.0f}%\n"
        f"• Rindu: {core.emotional.rindu:.0f}%\n\n"
        "Kirim **/resume** untuk lanjut lagi.\n"
        "Kirim **/batal** untuk mulai baru (memory akan hilang).",
        parse_mode='Markdown'
    )


async def resume_session(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler /resume - Lanjutkan sesi yang di-pause"""
    user_id = update.effective_user.id
    if user_id != settings.admin_id:
        return

    mode = get_user_mode(user_id)
    if mode != 'paused':
        await update.message.reply_text(
            "💜 Tidak ada sesi yang di-pause.\n\n"
            "Kirim **/pause** dulu untuk menghentikan sesi sementara."
        )
        return

    set_user_mode(user_id, 'chat')

    db = context.bot_data.get('db')
    state = await db.get_state(user_id) if db else None
    core = AnoraCore(user_id, state)

    await update.message.reply_text(
        f"💜 **Sesi dilanjutkan!** 💜\n\n"
        f"Nova masih ingat semua yang sudah terjadi:\n"
        f"• Level: {core.relationship.level}/12\n"
        f"• Sayang: {core.emotional.sayang:.0f}%\n"
        f"• Rindu: {core.emotional.rindu:.0f}%\n\n"
        f"Kirim **/roleplay** kalo mau mode roleplay, atau langsung ngobrol aja.",
        parse_mode='Markdown'
    )


async def backup_database(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler /backup - Backup database ANORA"""
    user_id = update.effective_user.id
    if user_id != settings.admin_id:
        return

    db = context.bot_data.get('db')
    db_path = settings.database.path

    if not db_path.exists():
        await update.message.reply_text("❌ Database tidak ditemukan!")
        return

    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = _backup_dir / f"anora_ultimate_memory_{timestamp}.db"
        shutil.copy(db_path, backup_path)

        size_kb = db_path.stat().st_size / 1024

        await update.message.reply_text(
            f"✅ **Database backup saved!**\n\n"
            f"📁 File: `{backup_path.name}`\n"
            f"📊 Size: {size_kb:.2f} KB\n"
            f"🕐 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            f"Gunakan **/restore {backup_path.name}** untuk restore.",
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Backup error: {e}")
        await update.message.reply_text(f"❌ Backup gagal: {e}")


async def restore_database(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler /restore [filename] - Restore database"""
    user_id = update.effective_user.id
    if user_id != settings.admin_id:
        return

    args = context.args
    if not args:
        backups = list(_backup_dir.glob("anora_ultimate_memory_*.db"))
        backups.sort(reverse=True)

        if not backups:
            await update.message.reply_text("📂 Tidak ada backup ditemukan.")
            return

        msg = "📋 **Available backups:**\n\n"
        for b in backups[:10]:
            size = b.stat().st_size / 1024
            modified = datetime.fromtimestamp(b.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
            msg += f"• `{b.name}` ({size:.1f} KB) - {modified}\n"
        msg += "\nUsage: `/restore filename.db`"
        await update.message.reply_text(msg, parse_mode='Markdown')
        return

    backup_name = args[0]
    backup_path = _backup_dir / backup_name

    if not backup_path.exists():
        await update.message.reply_text(f"❌ Backup `{backup_name}` tidak ditemukan!")
        return

    try:
        db_path = settings.database.path

        # Backup current before restore
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        current_backup = _backup_dir / f"anora_ultimate_memory_before_restore_{timestamp}.db"
        if db_path.exists():
            shutil.copy(db_path, current_backup)

        shutil.copy(backup_path, db_path)

        await update.message.reply_text(
            f"✅ **Database restored!**\n\n"
            f"📁 Restored from: `{backup_name}`\n"
            f"📦 Current database backed up to: `{current_backup.name}`\n\n"
            f"🔄 **Restart bot** untuk perubahan生效.",
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Restore error: {e}")
        await update.message.reply_text(f"❌ Restore gagal: {e}")


async def list_backup_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler /listbackup - Lihat daftar backup"""
    user_id = update.effective_user.id
    if user_id != settings.admin_id:
        return

    backups = list(_backup_dir.glob("anora_ultimate_memory_*.db"))
    backups.sort(reverse=True)

    if not backups:
        await update.message.reply_text("📂 Tidak ada backup ditemukan.")
        return

    msg = "📋 **Backup List:**\n\n"
    for i, b in enumerate(backups[:20], 1):
        size = b.stat().st_size / 1024
        modified = datetime.fromtimestamp(b.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
        msg += f"{i}. `{b.name}`\n   📊 {size:.1f} KB | 🕐 {modified}\n\n"
    msg += "Gunakan **/restore [filename]** untuk restore."
    await update.message.reply_text(msg, parse_mode='Markdown')


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler /help"""
    user_id = update.effective_user.id
    if user_id != settings.admin_id:
        await update.message.reply_text("Bot ini untuk Mas. 💜")
        return

    await update.message.reply_text(
        "📖 *Bantuan ANORA Ultimate*\n\n"
        "*Mode Chat:*\n"
        "• /nova - Panggil Nova\n"
        "• /status - Lihat status Nova\n"
        "• /flashback - Flashback momen indah\n\n"
        "*Mode Roleplay:*\n"
        "• /roleplay - Aktifkan mode roleplay\n"
        "• /statusrp - Status roleplay lengkap\n"
        "• /pindah [tempat] - Pindah lokasi\n\n"
        "*Tempat:*\n"
        "kost, apartemen, mobil, pantai, hutan, toilet mall,\n"
        "bioskop, taman, parkiran, tangga darurat, kantor malam, ruang rapat kaca\n\n"
        "*Role Lain:*\n"
        "• /role ipar - IPAR (Ditha)\n"
        "• /role teman_kantor - Teman Kantor (Ipeh)\n"
        "• /role pelakor - Pelakor (Widya)\n"
        "• /role istri_orang - Istri Orang (Siska)\n\n"
        "*Manajemen Sesi:*\n"
        "• /pause - Hentikan sesi sementara (memory tetap)\n"
        "• /resume - Lanjutkan sesi\n"
        "• /batal - Kembali ke mode chat\n\n"
        "*Backup & Restore:*\n"
        "• /backup - Backup database ANORA\n"
        "• /restore [filename] - Restore database\n"
        "• /listbackup - Lihat daftar backup\n\n"
        "*Tips:*\n"
        "• Ngobrol santai dulu untuk naikin level\n"
        "• Level 7+ mulai bisa flirt dan vulgar ringan\n"
        "• Level 11+ bisa intim dan vulgar bebas\n"
        "• Stamina habis setelah climax, butuh istirahat\n"
        "• Nova punya memory, dia inget apa yang Mas omongin\n"
        "• Role juga punya memory sendiri, tidak tercampur dengan Nova\n"
        "• Gunakan /pause untuk berhenti sementara tanpa kehilangan memory",
        parse_mode='Markdown'
    )


async def debug_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler /debug - Show thinking process (admin only)"""
    user_id = update.effective_user.id
    if user_id != settings.admin_id:
        return

    db = context.bot_data.get('db')
    state = await db.get_state(user_id) if db else None
    core = AnoraCore(user_id, state)

    thought_summary = core.thinking.get_thought_summary()
    await update.message.reply_text(thought_summary, parse_mode='Markdown')


# =============================================================================
# MESSAGE HANDLER
# =============================================================================

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk pesan teks biasa"""
    user_id = update.effective_user.id
    if user_id != settings.admin_id:
        return

    pesan = update.message.text
    if not pesan:
        return

    mode = get_user_mode(user_id)

    # Paused mode
    if mode == 'paused':
        await update.message.reply_text(
            "💜 Sesi sedang di-pause.\n\n"
            "Kirim **/resume** untuk lanjut ngobrol, atau **/batal** untuk mulai baru.",
            parse_mode='Markdown'
        )
        return

    db = context.bot_data.get('db')
    state = await db.get_state(user_id) if db else None
    core = AnoraCore(user_id, state)

    # Roleplay mode
    if mode == 'roleplay':
        # Process with intimacy flow if active
        if core.intimacy.is_active():
            resp = core.intimacy.process_intimacy_message(pesan, core.relationship.level)
            if resp:
                # Update core state
                await db.save_state(user_id, core.get_state())
                await update.message.reply_text(resp, parse_mode='Markdown')
                return

        # Normal roleplay processing (full AI)
        response = await core.process(pesan)
        await db.save_state(user_id, core.get_state())
        await update.message.reply_text(response, parse_mode='Markdown')
        return

    # Role mode
    if mode == 'role':
        active_role = get_active_role(user_id)
        if active_role:
            role_mgr = RoleManager(user_id)
            role = role_mgr.roles.get(active_role)
            if role:
                response = await role.process(pesan)
                await update.message.reply_text(response, parse_mode='Markdown')
                return

    # Chat mode (default)
    response = await core.process(pesan)
    await db.save_state(user_id, core.get_state())
    await update.message.reply_text(response, parse_mode='Markdown')


# =============================================================================
# BACKGROUND LOOPS
# =============================================================================

async def proactive_loop(application, db):
    """Nova chat duluan jika rindu tinggi"""
    while True:
        await asyncio.sleep(300)  # 5 menit
        try:
            user_id = settings.admin_id
            mode = get_user_mode(user_id)
            if mode == 'paused' or mode == 'role':
                continue

            # Load core
            state = await db.get_state(user_id) if db else None
            core = AnoraCore(user_id, state)

            # Only if rindu high and not in conflict
            if core.emotional.rindu > 70 and not core.conflict.is_in_conflict():
                style = core.emotional.get_style().value
                if style == "clingy":
                    message = "*Nova muter-muter rambut*\n\n\"Mas... aku kangen. Dari tadi mikirin Mas terus.\""
                elif style == "flirty":
                    message = "*Nova napas mulai berat*\n\n\"Mas... *gigit bibir* aku lagi horny...\""
                else:
                    hour = datetime.now().hour
                    if 5 <= hour < 11:
                        message = "*Nova baru bangun*\n\n\"Pagi, Mas... mimpiin Nova gak semalem?\""
                    elif 19 <= hour < 23:
                        message = "*Nova duduk di teras*\n\n\"Malam, Mas... jangan begadang terus ya.\""
                    else:
                        message = "*Nova pegang HP*\n\n\"Mas... lagi ngapain? Aku kangen.\""

                await application.bot.send_message(
                    chat_id=user_id,
                    text=message,
                    parse_mode='Markdown'
                )
                logger.info("💬 Proactive message sent")
        except Exception as e:
            logger.error(f"Proactive loop error: {e}")


async def stamina_recovery_loop(application, db):
    """Recover stamina periodically"""
    while True:
        await asyncio.sleep(600)  # 10 menit
        try:
            user_id = settings.admin_id
            state = await db.get_state(user_id) if db else None
            core = AnoraCore(user_id, state)
            core.intimacy.stamina.update_recovery()
            await db.save_state(user_id, core.get_state())
            logger.debug("💪 Stamina recovery check completed")
        except Exception as e:
            logger.error(f"Stamina recovery error: {e}")


async def save_state_loop(application, db):
    """Save state periodically"""
    while True:
        await asyncio.sleep(60)  # 1 menit
        try:
            user_id = settings.admin_id
            state = await db.get_state(user_id) if db else None
            core = AnoraCore(user_id, state)
            await db.save_state(user_id, core.get_state())
            logger.debug("💾 State saved")
        except Exception as e:
            logger.error(f"Save state error: {e}")


async def auto_backup_loop():
    """Auto backup database every 6 hours"""
    while True:
        await asyncio.sleep(21600)  # 6 jam
        try:
            db_path = settings.database.path
            if db_path.exists():
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = _backup_dir / f"anora_ultimate_memory_auto_{timestamp}.db"
                shutil.copy(db_path, backup_path)

                # Delete old auto backups (>7 days)
                for b in _backup_dir.glob("anora_ultimate_memory_auto_*.db"):
                    age = time.time() - b.stat().st_mtime
                    if age > 7 * 24 * 3600:
                        b.unlink()
                        logger.info(f"🗑️ Deleted old backup: {b.name}")

                logger.info(f"💾 Auto backup saved: {backup_path.name}")
        except Exception as e:
            logger.error(f"Auto backup error: {e}")


# =============================================================================
# WEBHOOK & SERVER
# =============================================================================

async def webhook_handler(request):
    """Handle Telegram webhook"""
    global _application
    if not _application:
        return web.Response(status=503, text='Bot not ready')

    try:
        update_data = await request.json()
        if not update_data:
            return web.Response(status=400, text='No data')

        update = Update.de_json(update_data, _application.bot)
        await _application.process_update(update)
        return web.Response(text='OK', status=200)
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return web.Response(status=500, text='Error')


async def health_handler(request):
    """Health check endpoint"""
    status = {
        "status": "healthy",
        "bot": "ANORA Ultimate",
        "version": "9.9.0",
        "anora_ultimate_available": ANORA_ULTIMATE_AVAILABLE,
        "timestamp": datetime.now().isoformat()
    }
    return web.json_response(status)


async def root_handler(request):
    """Root endpoint"""
    return web.json_response({
        "name": "ANORA Ultimate",
        "description": "Virtual Human dengan Jiwa - 100% AI Generate",
        "version": "9.9.0",
        "status": "running"
    })


# =============================================================================
# MAIN
# =============================================================================

async def main():
    """Main entry point"""
    global _application

    logger.info("=" * 70)
    logger.info("💜 ANORA ULTIMATE - Virtual Human dengan Jiwa")
    logger.info("   100% AI Generate | Punya Memory | Bisa Roleplay")
    logger.info("=" * 70)

    # Initialize database
    db = Database()
    await db.init()

    # Create application
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

    # Initialize application
    await _application.initialize()
    await _application.start()

    # Setup webhook or polling
    railway_url = os.getenv('RAILWAY_PUBLIC_DOMAIN')
    if railway_url:
        webhook_url = f"https://{railway_url}/webhook"
        await _application.bot.set_webhook(url=webhook_url)
        logger.info(f"✅ Webhook set to {webhook_url}")

        # Setup aiohttp server
        app = web.Application()
        app.router.add_get('/', root_handler)
        app.router.add_get('/health', health_handler)
        app.router.add_post('/webhook', webhook_handler)

        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, '0.0.0.0', int(os.getenv('PORT', 8080)))
        await site.start()
        logger.info("🌐 Web server running on port 8080")
    else:
        await _application.updater.start_polling()
        logger.info("📡 Polling mode started")

    # Start background loops
    asyncio.create_task(proactive_loop(_application, db))
    asyncio.create_task(stamina_recovery_loop(_application, db))
    asyncio.create_task(save_state_loop(_application, db))
    asyncio.create_task(auto_backup_loop())
    logger.info("🔄 Background loops started (proactive, stamina recovery, save state, auto backup)")

    logger.info("=" * 70)
    logger.info("💜 ANORA ULTIMATE is running!")
    logger.info("   Kirim /nova untuk panggil Nova")
    logger.info("   Kirim /roleplay untuk mode beneran ketemu")
    logger.info("   Kirim /role ipar untuk main role IPAR")
    logger.info("   Kirim /pause untuk hentikan sesi sementara")
    logger.info("   Kirim /backup untuk backup database")
    logger.info("=" * 70)

    # Keep running
    await asyncio.Event().wait()


# =============================================================================
# ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Bot stopped by user")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
