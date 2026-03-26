# app/config.py
"""
ANORA Ultimate - Configuration
Version: 9.9.0
"""

import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)


class WebhookSettings(BaseSettings):
    """Konfigurasi webhook untuk Railway"""
    model_config = {"env_prefix": "", "extra": "ignore"}

    port: int = Field(8000, alias="PORT")
    path: str = Field("/webhook", alias="WEBHOOK_PATH")
    secret_token: Optional[str] = Field(None, alias="WEBHOOK_SECRET")
    railway_domain: Optional[str] = Field(None, alias="RAILWAY_PUBLIC_DOMAIN")
    railway_static_url: Optional[str] = Field(None, alias="RAILWAY_STATIC_URL")

    @property
    def url(self) -> Optional[str]:
        if self.railway_domain:
            return f"https://{self.railway_domain}{self.path}"
        if self.railway_static_url:
            return f"https://{self.railway_static_url}{self.path}"
        return None

    @property
    def is_railway(self) -> bool:
        return bool(self.railway_domain or self.railway_static_url)


class DatabaseSettings(BaseSettings):
    """Konfigurasi database"""
    model_config = {"env_prefix": "DB_", "extra": "ignore"}

    type: str = Field("sqlite", alias="TYPE")
    path: Path = Field(Path("data/anora_ultimate.db"), alias="PATH")
    pool_size: int = Field(5, alias="POOL_SIZE")
    timeout: int = Field(30, alias="TIMEOUT")

    @property
    def url(self) -> str:
        return f"sqlite+aiosqlite:///{self.path}"

    @field_validator('path', mode='before')
    @classmethod
    def validate_path(cls, v):
        if isinstance(v, str):
            return Path(v)
        return v


class AISettings(BaseSettings):
    """Konfigurasi AI DeepSeek"""
    model_config = {"env_prefix": "AI_", "extra": "ignore"}

    temperature: float = Field(0.85, alias="TEMPERATURE")
    max_tokens: int = Field(1200, alias="MAX_TOKENS")
    timeout: int = Field(45, alias="TIMEOUT")
    model: str = Field("deepseek-chat", alias="MODEL")

    @field_validator('temperature')
    @classmethod
    def validate_temperature(cls, v):
        if not 0 <= v <= 2:
            raise ValueError(f'Temperature must be between 0 and 2, got {v}')
        return v


class LevelSettings(BaseSettings):
    """Konfigurasi level system untuk Realism 9.9"""
    model_config = {"env_prefix": "", "extra": "ignore"}

    # Level thresholds (interaction count needed to reach next level)
    level_targets: Dict[int, int] = {
        1: 7, 2: 15, 3: 25, 4: 35, 5: 45,
        6: 55, 7: 65, 8: 75, 9: 85, 10: 95,
        11: 110, 12: 130
    }

    # Level names
    level_names: Dict[int, str] = {
        1: "Malu-malu", 2: "Mulai terbuka", 3: "Goda-godaan",
        4: "Dekat", 5: "Sayang", 6: "PACAR/PDKT",
        7: "Nyaman", 8: "Eksplorasi", 9: "Bergairah",
        10: "Passionate", 11: "Soul Bounded", 12: "Aftercare"
    }

    # Vulgar unlock threshold
    vulgar_start_level: int = Field(7, alias="VULGAR_START_LEVEL")
    vulgar_full_level: int = Field(11, alias="VULGAR_FULL_LEVEL")

    # Stamina limits per session
    max_climax_nova: int = Field(5, alias="MAX_CLIMAX_NOVA")
    max_climax_mas: int = Field(2, alias="MAX_CLIMAX_MAS")
    cooldown_minutes: int = Field(30, alias="COOLDOWN_MINUTES")

    # Intimacy settings per level
    level_11_foreplay_target: int = Field(12, alias="LEVEL_11_FOREPLAY_TARGET")
    level_11_climax_target: int = Field(6, alias="LEVEL_11_CLIMAX_TARGET")
    level_12_foreplay_target: int = Field(15, alias="LEVEL_12_FOREPLAY_TARGET")
    level_12_climax_target: int = Field(8, alias="LEVEL_12_CLIMAX_TARGET")

    # Arousal gain modifiers
    level_11_arousal_gain: float = Field(0.15, alias="LEVEL_11_AROUSAL_GAIN")
    level_12_arousal_gain: float = Field(0.12, alias="LEVEL_12_AROUSAL_GAIN")

    # Temperature for creativity
    level_11_temperature: float = Field(0.95, alias="LEVEL_11_TEMPERATURE")
    level_12_temperature: float = Field(0.95, alias="LEVEL_12_TEMPERATURE")

    def get_level_config(self, level: int) -> Dict[str, Any]:
        if level >= 12:
            return {
                'min_sentences': 6, 'max_sentences': 12, 'max_chars': 1800,
                'arousal_cap': 100, 'arousal_gain': self.level_12_arousal_gain,
                'temperature': self.level_12_temperature, 'vulgar_mode': True,
                'foreplay_target': self.level_12_foreplay_target,
                'climax_target': self.level_12_climax_target,
            }
        elif level >= 11:
            return {
                'min_sentences': 6, 'max_sentences': 10, 'max_chars': 1500,
                'arousal_cap': 100, 'arousal_gain': self.level_11_arousal_gain,
                'temperature': self.level_11_temperature, 'vulgar_mode': True,
                'foreplay_target': self.level_11_foreplay_target,
                'climax_target': self.level_11_climax_target,
            }
        else:
            return {
                'min_sentences': 2, 'max_sentences': 6, 'max_chars': 1200,
                'arousal_cap': 80, 'arousal_gain': 0.1,
                'temperature': 0.85, 'vulgar_mode': False,
                'foreplay_target': 25, 'climax_target': 12,
            }


class MemorySettings(BaseSettings):
    """Konfigurasi memory system"""
    model_config = {"env_prefix": "MEMORY_", "extra": "ignore"}

    working_memory_size: int = Field(50, alias="WORKING_SIZE")
    long_term_memory_size: int = Field(200, alias="LONG_TERM_SIZE")
    memory_dir: Path = Field(Path("data/memory"), alias="DIR")


class FeatureSettings(BaseSettings):
    """Feature toggles"""
    model_config = {"env_prefix": "FEATURE_", "extra": "ignore"}

    sexual_content_enabled: bool = Field(True, alias="SEXUAL_CONTENT")
    proactive_chat_enabled: bool = Field(True, alias="PROACTIVE_CHAT")
    flashback_enabled: bool = Field(True, alias="FLASHBACK")
    aftercare_enabled: bool = Field(True, alias="AFTERCARE")
    roleplay_roles_enabled: bool = Field(True, alias="ROLES")
    debug_mode: bool = Field(False, alias="DEBUG_MODE")


class BackupSettings(BaseSettings):
    """Konfigurasi backup"""
    model_config = {"env_prefix": "BACKUP_", "extra": "ignore"}

    enabled: bool = Field(True, alias="ENABLED")
    interval_hours: int = Field(6, alias="INTERVAL_HOURS")
    retention_days: int = Field(7, alias="RETENTION_DAYS")
    backup_dir: Path = Field(Path("data/backups"), alias="DIR")


class Settings(BaseSettings):
    """Main settings"""
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore"
    }

    deepseek_api_key: str = Field(..., alias="DEEPSEEK_API_KEY")
    telegram_token: str = Field(..., alias="TELEGRAM_TOKEN")
    admin_id: int = Field(..., alias="ADMIN_ID")

    webhook: WebhookSettings = WebhookSettings()
    database: DatabaseSettings = DatabaseSettings()
    ai: AISettings = AISettings()
    level: LevelSettings = LevelSettings()
    memory: MemorySettings = MemorySettings()
    features: FeatureSettings = FeatureSettings()
    backup: BackupSettings = BackupSettings()

    @field_validator('deepseek_api_key')
    @classmethod
    def validate_deepseek_key(cls, v):
        if not v or v == "your_deepseek_api_key_here":
            raise ValueError("DEEPSEEK_API_KEY tidak boleh kosong")
        return v

    @field_validator('telegram_token')
    @classmethod
    def validate_telegram_token(cls, v):
        if not v or v == "your_telegram_bot_token_here":
            raise ValueError("TELEGRAM_TOKEN tidak boleh kosong")
        return v

    @field_validator('admin_id')
    @classmethod
    def validate_admin_id(cls, v):
        if v == 0:
            logger.warning("⚠️ ADMIN_ID = 0. Admin commands won't work.")
        return v

    def create_directories(self):
        dirs = [
            self.memory.memory_dir,
            self.backup.backup_dir,
            self.database.path.parent,
            Path("data"),
        ]
        for dir_path in dirs:
            dir_path.mkdir(parents=True, exist_ok=True)
        return self

    def log_configuration(self):
        logger.info("=" * 70)
        logger.info("💜 ANORA ULTIMATE - Configuration Loaded")
        logger.info("=" * 70)
        logger.info(f"🗄️  Database: {self.database.url}")
        logger.info(f"🤖 AI Model: {self.ai.model} | Temperature: {self.ai.temperature}")
        logger.info(f"👑 Admin ID: {self.admin_id}")
        logger.info(f"📊 Working Memory: {self.memory.working_memory_size} chats")
        logger.info(f"💕 Level 10: {self.level.level_targets[10]} chats")
        logger.info(f"🔥 Soul Bounded (Level 11): {self.level.level_targets[11]} chats")
        logger.info(f"💤 Aftercare (Level 12): {self.level.level_targets[12]} chats")
        logger.info(f"💋 Vulgar Start: Level {self.level.vulgar_start_level} | Full: Level {self.level.vulgar_full_level}")
        logger.info(f"💪 Max Climax per session: Nova {self.level.max_climax_nova}x | Mas {self.level.max_climax_mas}x")
        logger.info(f"🌍 Railway Mode: {self.webhook.is_railway}")
        if self.webhook.url:
            logger.info(f"🌐 Webhook URL: {self.webhook.url}")
        logger.info("=" * 70)


_settings: Optional[Settings] = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
        _settings.create_directories()
        _settings.log_configuration()
    return _settings


settings = get_settings()
