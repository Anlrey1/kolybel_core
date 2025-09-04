# agents.py — гибридная система агентов (n8n + автономные)
import os
import logging
import requests
from datetime import datetime
from typing import Dict, Optional
from llm import ask_llm_with_context
from memory_core import MemoryCore
from config import (
    TELEGRAM_TOKEN,
    TELEGRAM_CHANNEL_ID,
    TELEGRAM_ADMIN_ID,
)
from template_engine import generate_from_template
from autonomous_agents import create_autonomous_agent_from_plan, get_agent_manager

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Конфигурация n8n (опциональная)
N8N_API = os.getenv("N8N_API_URL", "")
N8N_AUTH = (os.getenv("N8N_USER", ""), os.getenv("N8N_PASSWORD", ""))
PROMO_BUDGET = int(os.getenv("PROMO_BUDGET", "0"))


def create_agent_from_plan(
    memory: MemoryCore,
    rss_url: str = "https://dtf.ru/rss",
    chat_id: str = "-1002669388680",
    style: str = "в стиле для подростков до 18 лет",
    use_n8n: bool = None,
) -> str:
    """
    Создает агента: сначала пытается n8n, при неудаче создает автономного
    """
    # Автоматически определяем, использовать ли n8n
    if use_n8n is None:
        use_n8n = bool(N8N_API and N8N_AUTH[0])

    if use_n8n:
        try:
            return _create_n8n_agent(memory, rss_url, chat_id, style)
        except Exception as e:
            logger.warning(f"Не удалось создать n8n агента: {e}")
            logger.info("Переключаемся на автономного агента...")

    # Создаем автономного агента
    return create_autonomous_agent_from_plan(
        memory=memory,
        agent_type="rss_monitor",
        name=f"RSS Monitor ({rss_url.split('/')[-2] if '/' in rss_url else 'RSS'})",
        rss_url=rss_url,
        chat_id=chat_id,
        style=style,
        schedule="0 9,15,20 * * *"
    )


def _create_n8n_agent(
    memory: MemoryCore,
    rss_url: str,
    chat_id: str,
    style: str
) -> str:
    """
    Создает агента n8n (оригинальная логика)
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
    logger.info(f"Создан n8n агент: {result[:100]}...")

    memory.store(f"[agent] {result}")

    os.makedirs("approved_goals", exist_ok=True)
    agent_filename = f"n8n_agent_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    agent_path = os.path.join("approved_goals", agent_filename)

    with open(agent_path, "w", encoding="utf-8") as f:
        f.write(result)

    # Публикуем в n8n
    headers = {"Content-Type": "application/json"}
    response = requests.post(
        N8N_API,
        auth=N8N_AUTH,
        headers=headers,
        data=result.encode("utf-8"),
        timeout=30,
    )

    if response.status_code == 200:
        logger.info("N8N агент успешно опубликован")
        log_agent_usage(agent_filename, True)

        # Автоматически добавляем продвижение
        if PROMO_BUDGET > 0:
            add_promotion_workflow(agent_path, chat_id)
    else:
        logger.error(f"Ошибка публикации в n8n: {response.status_code}")
        log_agent_usage(agent_filename, False)
        raise Exception(f"N8N API error: {response.status_code}")

    return agent_path


def create_content_agent(
    memory: MemoryCore,
    template_id: str,
    chat_id: str,
    topics: list = None,
    schedule: str = "every 4 hours"
) -> str:
    """
    Создает автономного агента для генерации контента
    """
    config = {
        "name": f"Content Generator ({template_id})",
        "description": f"Генерация контента по шаблону {template_id}",
        "type": "content_generator",
        "schedule": schedule,
        "config": {
            "template_id": template_id,
            "chat_id": chat_id,
            "topics": topics or []
        }
    }

    manager = get_agent_manager(memory)
    agent_id = manager.create_agent(config)

    if not manager.is_running:
        manager.start_scheduler()

    logger.info(f"Создан агент генерации контента: {agent_id}")
    return agent_id


def create_channel_manager_agent(
    memory: MemoryCore,
    chat_id: str,
    actions: list = None
) -> str:
    """
    Создает автономного агента для управления каналом
    """
    config = {
        "name": f"Channel Manager ({chat_id})",
        "description": f"Управление каналом {chat_id}",
        "type": "channel_manager",
        "schedule": "0 12 * * *",  # Раз в день в 12:00
        "config": {
            "chat_id": chat_id,
            "actions": actions or ["analytics", "engagement"]
        }
    }

    manager = get_agent_manager(memory)
    agent_id = manager.create_agent(config)

    if not manager.is_running:
        manager.start_scheduler()

    logger.info(f"Создан агент управления каналом: {agent_id}")
    return agent_id


def get_agents_status(memory: MemoryCore) -> Dict:
    """
    Получение статуса всех агентов (n8n + автономные)
    """
    manager = get_agent_manager(memory)
    autonomous_agents = manager.list_agents()

    # Добавляем информацию о n8n агентах из файлов
    n8n_agents = []
    if os.path.exists("approved_goals"):
        for filename in os.listdir("approved_goals"):
            if filename.startswith("n8n_agent_") and filename.endswith(".json"):
                n8n_agents.append({
                    "id": filename,
                    "name": f"N8N Agent ({filename})",
                    "type": "n8n_workflow",
                    "is_active": True,  # Предполагаем, что активен
                    "platform": "n8n"
                })

    return {
        "autonomous_agents": autonomous_agents,
        "n8n_agents": n8n_agents,
        "total_agents": len(autonomous_agents) + len(n8n_agents),
        "autonomous_count": len(autonomous_agents),
        "n8n_count": len(n8n_agents),
        "scheduler_running": manager.is_running
    }


def start_autonomous_system(memory: MemoryCore):
    """
    Запуск автономной системы агентов
    """
    manager = get_agent_manager(memory)
    if not manager.is_running:
        manager.start_scheduler()
        logger.info("🚀 Автономная система агентов запущена")
    else:
        logger.info("ℹ️ Автономная система уже работает")


def stop_autonomous_system(memory: MemoryCore):
    """
    Остановка автономной системы агентов
    """
    manager = get_agent_manager(memory)
    if manager.is_running:
        manager.stop_scheduler()
        logger.info("⏹️ Автономная система агентов остановлена")

# ... existing code ...


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
                    "schedule": "0 18 * * 0",  # Раз в неделю в воскресенье
                },
            },
        ]
    }

    try:
        promo_filename = agent_path.replace(".json", "_promo.json")
        with open(promo_filename, "w", encoding="utf-8") as f:
            import json
            json.dump(promo_workflow, f, ensure_ascii=False, indent=2)

        if N8N_API:
            headers = {"Content-Type": "application/json"}
            response = requests.post(
                N8N_API,
                auth=N8N_AUTH,
                headers=headers,
                json=promo_workflow,
                timeout=30,
            )
            return response.status_code == 200
        return True

    except Exception as e:
        logger.error(f"Ошибка создания промо-workflow: {e}")
        return False


def log_agent_usage(agent_name: str, success: bool):
    """
    Логирование использования агента
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    status = "SUCCESS" if success else "FAILED"

    os.makedirs("agent_logs", exist_ok=True)
    with open("agent_logs/usage.log", "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {agent_name}: {status}\n")


def audit_agents():
    """
    Аудит всех агентов (n8n + автономные)
    """
    print("🔍 Аудит агентов:")

    # N8N агенты
    n8n_count = 0
    if os.path.exists("approved_goals"):
        for name in os.listdir("approved_goals"):
            if name.startswith("n8n_agent_") and name.endswith(".json"):
                print(f"• [N8N] {name}")
                n8n_count += 1

    # Автономные агенты
    autonomous_count = 0
    if os.path.exists("autonomous_agents"):
        for name in os.listdir("autonomous_agents"):
            if name.endswith(".json"):
                print(f"• [AUTO] {name}")
                autonomous_count += 1

    print(
        f"\n📊 Итого: N8N агентов: {n8n_count}, Автономных: {autonomous_count}")

    # Статус планировщика
    try:
        from autonomous_agents import _agent_manager
        if _agent_manager and _agent_manager.is_running:
            print("✅ Планировщик автономных агентов: РАБОТАЕТ")
        else:
            print("⏸️ Планировщик автономных агентов: ОСТАНОВЛЕН")
    except:
        print("❓ Статус планировщика: НЕИЗВЕСТЕН")


def summarize_agent_performance():
    """
    Сводка производительности агентов
    """
    try:
        # Читаем логи использования
        usage_stats = {"success": 0, "failed": 0}
        if os.path.exists("agent_logs/usage.log"):
            with open("agent_logs/usage.log", "r", encoding="utf-8") as f:
                for line in f:
                    if "SUCCESS" in line:
                        usage_stats["success"] += 1
                    elif "FAILED" in line:
                        usage_stats["failed"] += 1

        total = usage_stats["success"] + usage_stats["failed"]
        success_rate = (usage_stats["success"] / max(1, total)) * 100

        # Автономные агенты
        autonomous_stats = ""
        try:
            from autonomous_agents import _agent_manager
            if _agent_manager:
                agents = _agent_manager.list_agents()
                active_count = len(
                    [a for a in agents if a.get("is_active", False)])
                autonomous_stats = f", Автономных активных: {active_count}/{len(agents)}"
        except:
            pass

        return f"📈 Статистика агентов: выполнено {usage_stats['success']}/{total}, успешность {success_rate:.1f}%{autonomous_stats}"

    except Exception as e:
        return f"📈 Статистика агентов: ошибка получения данных ({e})"
