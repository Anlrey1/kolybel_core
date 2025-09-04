# telegram_bridge.py — упрощенный мост для отправки сообщений
import requests
import logging
from typing import Optional
from config import TELEGRAM_TOKEN, TELEGRAM_API_BASE

logger = logging.getLogger(__name__)


def send_telegram_message(chat_id: str, text: str, parse_mode: str = "HTML") -> bool:
    """
    Отправка сообщения в Telegram канал/чат
    """
    if not TELEGRAM_TOKEN:
        logger.error("TELEGRAM_TOKEN не настроен")
        return False

    url = f"{TELEGRAM_API_BASE}/bot{TELEGRAM_TOKEN}/sendMessage"

    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": parse_mode,
        "disable_web_page_preview": False
    }

    try:
        response = requests.post(url, json=payload, timeout=30)

        if response.status_code == 200:
            logger.info(f"Сообщение отправлено в {chat_id}")
            return True
        else:
            logger.error(
                f"Ошибка отправки в Telegram: {response.status_code} - {response.text}")
            return False

    except Exception as e:
        logger.error(f"Исключение при отправке в Telegram: {e}")
        return False


def send_telegram_photo(chat_id: str, photo_url: str, caption: str = "") -> bool:
    """
    Отправка фото в Telegram канал/чат
    """
    if not TELEGRAM_TOKEN:
        logger.error("TELEGRAM_TOKEN не настроен")
        return False

    url = f"{TELEGRAM_API_BASE}/bot{TELEGRAM_TOKEN}/sendPhoto"

    payload = {
        "chat_id": chat_id,
        "photo": photo_url,
        "caption": caption,
        "parse_mode": "HTML"
    }

    try:
        response = requests.post(url, json=payload, timeout=30)

        if response.status_code == 200:
            logger.info(f"Фото отправлено в {chat_id}")
            return True
        else:
            logger.error(
                f"Ошибка отправки фото в Telegram: {response.status_code}")
            return False

    except Exception as e:
        logger.error(f"Исключение при отправке фото в Telegram: {e}")
        return False


def get_chat_info(chat_id: str) -> Optional[dict]:
    """
    Получение информации о чате/канале
    """
    if not TELEGRAM_TOKEN:
        return None

    url = f"{TELEGRAM_API_BASE}/bot{TELEGRAM_TOKEN}/getChat"

    try:
        response = requests.post(url, json={"chat_id": chat_id}, timeout=30)

        if response.status_code == 200:
            return response.json().get("result")
        else:
            logger.error(
                f"Ошибка получения информации о чате: {response.status_code}")
            return None

    except Exception as e:
        logger.error(f"Исключение при получении информации о чате: {e}")
        return None
