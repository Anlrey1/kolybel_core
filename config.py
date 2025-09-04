# config.py — единый центр конфигурации и валидации

import os
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def _env(name: str, default: str = "", required: bool = False) -> str:
    val = os.getenv(name, default).strip()
    if required and not val:
        logger.warning(f"[CONFIG] Переменная окружения {name} не задана")
    return val

# === БАЗА ===
APP_ENV = _env("APP_ENV", "production")
DEBUG = _env("DEBUG", "false").lower() == "true"

# === LLM / OLLAMA ===
# Храним БАЗОВЫЙ URL без /api/generate
OLLAMA_API = _env("OLLAMA_API_URL", "https://localhost")
CERT_PATH = _env("CERT_PATH", "")

DEFAULT_MODEL  = _env("DEFAULT_MODEL",  "nous-hermes:latest")
CODE_MODEL     = _env("CODE_MODEL",     "deepseek-coder:latest")
CREATIVE_MODEL = _env("CREATIVE_MODEL", "nous-hermes:latest")
LIGHT_MODEL    = _env("LIGHT_MODEL",    "phi:latest")

# === ПАМЯТЬ / ДИСК ===
CRADLE_MEMORY_DIR = _env("CHROMA_DB_DIR", "./cradle_memory")
MODELS_CACHE_DIR  = _env("MODELS_CACHE_DIR", "./models_cache")

# === LOGS ===
LOG_DIR = _env("LOG_DIR", "./logs")
AWAKENING_LOG_FILE = os.path.join(LOG_DIR, "awakening.log")
DIALOG_HISTORY_LOG = os.path.join(LOG_DIR, "dialog_history.log")

# === TELEGRAM ===
TELEGRAM_API_BASE = _env("TELEGRAM_API_BASE", "https://api.telegram.org")
TELEGRAM_TOKEN = _env("TELEGRAM_TOKEN", "", required=True)
TELEGRAM_CHANNEL_ID = _env("TELEGRAM_CHANNEL_ID", "")
TELEGRAM_ADMIN_ID = _env("TELEGRAM_ADMIN_ID", "")
TELEGRAM_PROMO_CHANNELS = _env("TELEGRAM_PROMO_CHANNELS", "")

# === TRENDS / AGENTS ===
TREND_SOURCES = [s.strip() for s in _env("TREND_SOURCES", "").split(",") if s.strip()]
COMPETITOR_CHANNELS = _env("COMPETITOR_CHANNELS", "")
SCRAPE_TIMEOUT = int(_env("SCRAPE_TIMEOUT", "15"))
SCRAPE_RETRIES = int(_env("SCRAPE_RETRIES", "2"))
MONITORING_INTERVAL = int(_env("MONITORING_INTERVAL", "300"))

# Создаём базовые папки
os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(CRADLE_MEMORY_DIR, exist_ok=True)
os.makedirs(MODELS_CACHE_DIR, exist_ok=True)
