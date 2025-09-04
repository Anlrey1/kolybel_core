# autonomous_agents.py — мост к новой архитектуре агентов
"""
Этот модуль обеспечивает обратную совместимость со старым API автономных агентов,
перенаправляя вызовы на новую архитектуру agents_v2.py

ВНИМАНИЕ: Этот API устарел. Используйте agents_v2.AgentManager для новых проектов.
"""

import logging
import warnings
from typing import Dict, List, Optional, Any

# Заглушки для отсутствующих модулей
try:
    from memory_core import MemoryCore
except ImportError:
    class MemoryCore:
        def store(self, content, metadata=None):
            print(f"[MEMORY] {content}")
        
        def get_similar(self, query, n_results=5):
            return []

# Импортируем новую архитектуру
from agents_v2 import AgentManager

logger = logging.getLogger(__name__)

# Показываем предупреждение об устаревшем API
warnings.warn(
    "Модуль autonomous_agents.py устарел. Используйте agents_v2.py для новой архитектуры агентов.",
    DeprecationWarning,
    stacklevel=2
)

def create_autonomous_agent_from_plan(
    memory: MemoryCore,
    agent_type: str,
    name: str,
    rss_url: str = "",
    chat_id: str = "",
    style: str = "информативный стиль",
    schedule: str = "0 9,15,20 * * *",
    **kwargs
) -> str:
    """
    Создает автономного агента (совместимость со старым API)
    
    ВНИМАНИЕ: Эта функция устарела. Используйте AgentManager.create_rss_agent() из agents_v2.py
    
    Args:
        memory: Система памяти
        agent_type: Тип агента ("rss_monitor", "content_generator")
        name: Имя агента
        rss_url: URL RSS ленты
        chat_id: ID Telegram чата
        style: Стиль генерации контента
        schedule: Расписание выполнения (cron формат)
        **kwargs: Дополнительные параметры
    
    Returns:
        str: ID созданного агента
    """
    logger.warning(
        f"Функция create_autonomous_agent_from_plan устарела. "
        f"Используйте AgentManager.create_rss_agent() из agents_v2.py"
    )
    
    # Получаем новый менеджер агентов
    new_manager = get_new_agent_manager()
    
    try:
        if agent_type == "rss_monitor":
            # Создаем RSS агента через новую архитектуру
            agent_id = new_manager.create_rss_agent(
                name=name,
                owner="legacy_user",
                rss_url=rss_url,
                telegram_chat_id=chat_id,
                schedule=schedule,
                style=style,
                runtime_preferences=["local", "n8n"]
            )
            
            logger.info(f"RSS агент '{name}' создан через новую архитектуру с ID {agent_id}")
            return agent_id
            
        elif agent_type == "content_generator":
            # Создаем контент агента через новую архитектуру
            template_id = kwargs.get("template_id", "default_template")
            topics = kwargs.get("topics", ["общие темы"])
            
            agent_id = new_manager.create_content_agent(
                name=name,
                owner="legacy_user",
                template_id=template_id,
                telegram_chat_id=chat_id,
                topics=topics,
                schedule=schedule,
                runtime_preferences=["local", "docker"]
            )
            
            logger.info(f"Контент агент '{name}' создан через новую архитектуру с ID {agent_id}")
            return agent_id
            
        else:
            raise ValueError(f"Неподдерживаемый тип агента: {agent_type}")
            
    except Exception as e:
        logger.error(f"Ошибка создания агента через новую архитектуру: {e}")
        
        # Fallback на устаревшую реализацию
        logger.warning("Переключение на устаревшую реализацию автономных агентов")
        
        try:
            from autonomous_agents_legacy import create_autonomous_agent_from_plan as legacy_create
            return legacy_create(
                memory=memory,
                agent_type=agent_type,
                name=name,
                rss_url=rss_url,
                chat_id=chat_id,
                style=style,
                schedule=schedule,
                **kwargs
            )
        except Exception as legacy_error:
            logger.error(f"Ошибка создания устаревшего агента: {legacy_error}")
            raise

def get_agent_manager():
    """
    Возвращает менеджер агентов (совместимость со старым API)

    ВНИМАНИЕ: Эта функция устарела. Используйте AgentManager из agents_v2.py
    """
    logger.warning(
        "Функция get_agent_manager() из autonomous_agents.py устарела. "
        "Используйте AgentManager из agents_v2.py"
    )

    try:
        # Возвращаем новый менеджер агентов
        return AgentManager()
    except Exception as e:
        logger.error(f"Ошибка получения нового менеджера агентов: {e}")

        # Fallback на устаревший менеджер
        logger.warning("Переключение на устаревший менеджер агентов")
        from autonomous_agents_legacy import get_agent_manager as get_legacy_manager
        return get_legacy_manager()

# Дополнительные функции для совместимости
class AgentTask:
    """Заглушка для старого класса AgentTask"""
    def __init__(self, *args, **kwargs):
        warnings.warn(
            "Класс AgentTask устарел. Используйте AgentSpecification из agent_specification.py",
            DeprecationWarning
        )

class BaseAgent:
    """Заглушка для старого класса BaseAgent"""
    def __init__(self, *args, **kwargs):
        warnings.warn(
            "Класс BaseAgent устарел. Используйте новую архитектуру из agents_v2.py",
            DeprecationWarning
        )

class RSSMonitorAgent:
    """Заглушка для старого класса RSSMonitorAgent"""
    def __init__(self, *args, **kwargs):
        warnings.warn(
            "Класс RSSMonitorAgent устарел. Используйте AgentManager.create_rss_agent() из agents_v2.py",
            DeprecationWarning
        )

# Информационное сообщение при импорте
logger.info(
    "Модуль autonomous_agents.py загружен в режиме совместимости. "
    "Все вызовы перенаправляются на новую архитектуру agents_v2.py. "
    "Рекомендуется обновить код для использования новой архитектуры."
)