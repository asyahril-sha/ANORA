# app/workers/background.py
"""
Background worker – periodic tasks: rindu growth, conflict decay, backup, proactive chat.
"""

import asyncio
import time
import logging
from pathlib import Path

from ..database.db import Database
from ..config import settings

logger = logging.getLogger(__name__)


async def start_worker(db: Database, bot):
    while True:
        try:
            # Backup
            if settings.backup.enabled:
                await auto_backup()

            # Proactive chat (skeleton)
            if settings.features.proactive_chat_enabled:
                await proactive_chat(db, bot)

            await asyncio.sleep(3600)  # 1 jam
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Worker error: {e}")
            await asyncio.sleep(60)


async def auto_backup():
    backup_dir = settings.backup.backup_dir
    backup_dir.mkdir(parents=True, exist_ok=True)
    import datetime
    today = datetime.date.today().isoformat()
    backup_file = backup_dir / f"anora_ultimate_{today}.db"
    db_path = settings.database.path
    if db_path.exists() and not backup_file.exists():
        import shutil
        shutil.copy(db_path, backup_file)
        logger.info(f"Backup created: {backup_file}")
    retention_days = settings.backup.retention_days
    cutoff = time.time() - (retention_days * 24 * 3600)
    for f in backup_dir.glob("anora_ultimate_*.db"):
        if f.stat().st_mtime < cutoff:
            f.unlink()
            logger.info(f"Deleted old backup: {f}")


async def proactive_chat(db: Database, bot):
    # TODO: ambil daftar user yang sudah lama tidak interaksi dan rindu > threshold
    pass
