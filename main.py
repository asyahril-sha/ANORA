# app/main.py
"""
FastAPI application for ANORA Ultimate.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from telegram import Bot

from .api.webhook import router as webhook_router, set_bot
from .database.db import Database
from .workers.background import start_worker
from .config import settings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting ANORA Ultimate...")
    db = Database()
    await db.init()
    app.state.db = db

    bot = Bot(token=settings.telegram_token)
    set_bot(bot)
    app.state.bot = bot

    worker_task = asyncio.create_task(start_worker(db, bot))

    yield

    worker_task.cancel()
    await db.close()
    logger.info("Shutdown complete.")


app = FastAPI(lifespan=lifespan)
app.include_router(webhook_router)


@app.get("/")
async def root():
    return {"status": "running", "name": "ANORA Ultimate", "version": "9.9.0"}


@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": __import__("time").time()}
