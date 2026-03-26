# app/database/db.py
"""
Database handler – SQLite dengan aiosqlite.
"""

import json
import time
import logging
import aiosqlite
from pathlib import Path
from typing import Optional, Dict

from ..config import settings

logger = logging.getLogger(__name__)


class Database:
    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = settings.database.path
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = None

    async def init(self):
        self._conn = await aiosqlite.connect(str(self.db_path))
        await self._conn.execute('''
            CREATE TABLE IF NOT EXISTS user_state (
                user_id INTEGER PRIMARY KEY,
                state TEXT NOT NULL,
                updated_at REAL NOT NULL
            )
        ''')
        await self._conn.commit()
        logger.info(f"Database initialized at {self.db_path}")

    async def get_state(self, user_id: int) -> Optional[Dict]:
        cursor = await self._conn.execute(
            "SELECT state FROM user_state WHERE user_id = ?", (user_id,)
        )
        row = await cursor.fetchone()
        if row:
            return json.loads(row[0])
        return None

    async def save_state(self, user_id: int, state: Dict):
        await self._conn.execute(
            "INSERT OR REPLACE INTO user_state (user_id, state, updated_at) VALUES (?, ?, ?)",
            (user_id, json.dumps(state), time.time())
        )
        await self._conn.commit()

    async def close(self):
        if self._conn:
            await self._conn.close()
