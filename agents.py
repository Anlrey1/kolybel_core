# agents.py
import os
import logging
import requests
from datetime import datetime
from typing import Dict, Optional
from llm import ask_llm_with_context
from memory_core import MemoryCore
from config import (
    N8N_API,
    N8N_AUTH,
    TELEGRAM_TOKEN,
    TELEGRAM_CHANNEL_ID,
    PROMO_BUDGET,
    TELEGRAM_ADMIN_ID,
)
from template_engine import generate_from_template

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_agent_from_plan(
    memory: MemoryCore,
    rss_url: str = "https://dtf.ru/rss",
    chat_id: str = "-1002669388680",
    style: str = "в стиле для подростков до 18 лет",
) -> str:
    """
    Создает агента n8n (сохраненная версия без изменений)
    """
    prompt = (
        f"Создай JSON-агента n8n, который выполняет следующие шаги:\n"
        f"- триггер по времени: 3 раза в день (в 9:00, 15:00, 20:00)\n"
        f"- получает новости из RSS: {rss_url}\n"
        f"- извлекает заголовки и ссылки на статьи\n"
        f"- обрабатывает текст через LLM, чтобы сделать стиль {style}\n"
        f"- публикует результат в Telegram-канал с chat_id {chat_id} через Telegram API\n\n"
        f"Структура должна быть в формате JSON n8n workflow. Выводи только JSON без пояснений."
    )

    result = ask_llm_with_context(prompt, model="mistral")
    logger.info(f"Создан агент: {result[:100]}...")  # Логируем начало JSON

    memory.store(f"[agent] {result}")

    os.makedirs("approved_goals", exist_ok=True)
    agent_filename = f"agent_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    agent_path = os.path.join("approved_goals", agent_filename)

    with open(agent_path, "w", encoding="utf-8") as f:
        f.write(result)

    try:
        headers = {"Content-Type": "application/json"}
        response = requests.post(
            N8N_API,
            auth=N8N_AUTH,
            headers=headers,
            data=result.encode("utf-8"),
            timeout=30,
        )

        if response.status_code == 200:
            logger.info("Агент успешно опубликован в n8n")
            log_agent_usage(agent_filename, True)

            # Автоматически добавляем продвижение
            if PROMO_BUDGET > 0:
                add_promotion_workflow(agent_path, chat_id)
        else:
            logger.error(f"Ошибка публикации: {response.status_code}")
            log_agent_usage(agent_filename, False)

    except Exception as e:
        logger.error(f"Исключение: {str(e)}")
        log_agent_usage(agent_filename, False)

    return agent_path


def add_promotion_workflow(agent_path: str, chat_id: str) -> bool:
    """
    Добавляет workflow продвижения для агента
    """
    promo_workflow = {
        "nodes": [
            {
                "type": "n8n-nodes-base.telegramSendMessage",
                "properties": {
                    "message": f"Новый канал: @{chat_id}\nАвтоматические посты о науке и технологиях!",
                    "chatIds": TELEGRAM_ADMIN_ID,
                    "schedule": "0 12 * * *",  # Раз в день в 12:00
                },
            },
            {
                "type": "n8n-nodes-base.telegramSendMessage",
                "properties": {
                    "message": "Присоединяйтесь к нашему новому каналу!",
                    "chatIds": ["@science", "@technews"],
                    "schedule": "0 18 * * 1,5",  # Пн и Пт в 18:00
                },
            },
        ]
    }

    try:
        response = requests.post(
            f"{N8N_API}/promo", auth=N8N_AUTH, json=promo_workflow, timeout=20
        )
        return response.status_code == 200
    except Exception as e:
        logger.error(f"Ошибка продвижения: {str(e)}")
        return False


def log_agent_usage(agent_name: str, result: bool) -> None:
    """
    Логирование использования агентов (без изменений)
    """
    os.makedirs("agent_logs", exist_ok=True)
    with open("agent_logs/usage.log", "a", encoding="utf-8") as f:
        f.write(
            f"{datetime.now().isoformat()} | {agent_name} | {'успех' if result else 'ошибка'}\n"
        )


def summarize_agent_performance() -> None:
    """
    Анализ эффективности агентов (без изменений)
    """
    stats = {}
    try:
        with open("agent_logs/usage.log", "r", encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split("|")
                if len(parts) == 3:
                    _, name, status = parts
                    name = name.strip()
                    status = status.strip()
                    if name not in stats:
                        stats[name] = {"успех": 0, "ошибка": 0}
                    stats[name][status] += 1

        print("📈 Эффективность агентов:")
        for name, count in stats.items():
            print(f"{name} — ✅ {count['успех']} / ❌ {count['ошибка']}")

    except FileNotFoundError:
        print("(логи пока отсутствуют)")


def track_competitor_channels() -> None:
    """
    Новая функция: отслеживание конкурентов
    """
    competitors = ["@sci", "@deep_tech", "@future_science"]
    for channel in competitors:
        try:
            # Здесь будет API для анализа каналов
            logger.info(f"Анализируем конкурента: {channel}")
        except Exception as e:
            logger.error(f"Ошибка анализа {channel}: {str(e)}")


def create_channel_agent(channel_theme: str) -> Dict:
    """
    Новая функция: комплексное создание канала
    """
    workflow = {
        "nodes": [
            {
                "type": "n8n-nodes-base.telegramCreateChannel",
                "properties": {
                    "title": f"{channel_theme} | Колыбель",
                    "description": "Автоматический канал, созданный ИИ",
                    "public": True,
                },
            },
            {
                "type": "n8n-nodes-base.telegramPost",
                "properties": {
                    "schedule": "0 9,15,20 * * *",
                    "contentType": "adaptive",
                },
            },
            {
                "type": "n8n-nodes-base.telegramPromote",
                "properties": {
                    "budget": PROMO_BUDGET,
                    "targetChannels": ["@science", "@technews"],
                },
            },
        ]
    }

    try:
        response = requests.post(N8N_API, auth=N8N_AUTH, json=workflow, timeout=30)
        return response.json()
    except Exception as e:
        logger.error(f"Ошибка создания канала: {str(e)}")
        return {"status": "error", "message": str(e)}
