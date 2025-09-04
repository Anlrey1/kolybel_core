# autonomous_agents_legacy.py — устаревшая система автономных агентов (для совместимости)
# Этот файл сохранен для обратной совместимости и будет постепенно выведен из использования

import os
import json
import time
import threading
import schedule
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, asdict
from abc import ABC, abstractmethod

# Заглушки для отсутствующих модулей
try:
    from memory_core import MemoryCore
except ImportError:
    class MemoryCore:
        def store(self, content, metadata=None):
            print(f"[MEMORY] {content}")

try:
    from llm import ask_llm_with_context
except ImportError:
    def ask_llm_with_context(prompt, model="mistral"):
        return f"[LLM STUB] Generated response for: {prompt[:50]}..."

try:
    from template_engine import generate_from_template
except ImportError:
    def generate_from_template(template_id, context):
        return f"[TEMPLATE STUB] Generated content from {template_id}"

try:
    from telegram_bridge import send_telegram_message
except ImportError:
    def send_telegram_message(chat_id, message):
        print(f"[TELEGRAM STUB] Send to {chat_id}: {message[:100]}...")
        return True

logger = logging.getLogger(__name__)

@dataclass
class AgentTask:
    """Базовая структура задачи агента (устаревшая)"""
    id: str
    name: str
    description: str
    schedule_pattern: str
    task_type: str
    config: Dict
    is_active: bool = True
    created_at: str = ""
    last_run: str = ""
    success_count: int = 0
    error_count: int = 0

class BaseAgent(ABC):
    """Базовый класс для всех автономных агентов (устаревший)"""
    
    def __init__(self, task: AgentTask, memory: MemoryCore):
        self.task = task
        self.memory = memory
        self.logger = logging.getLogger(f"LegacyAgent.{task.name}")
        
        # Предупреждение об устаревшем API
        self.logger.warning(f"Используется устаревший API автономных агентов для {task.name}. "
                          "Рекомендуется мигрировать на новую архитектуру agents_v2.py")
    
    @abstractmethod
    def execute(self) -> bool:
        """Выполнить задачу агента. Возвращает True при успехе"""
        pass
    
    def log_execution(self, success: bool, message: str = ""):
        """Логирование выполнения задачи"""
        timestamp = datetime.now().isoformat()
        status = "SUCCESS" if success else "ERROR"
        
        log_entry = {
            "agent_id": self.task.id,
            "timestamp": timestamp,
            "status": status,
            "message": message,
            "legacy_agent": True
        }
        
        self.memory.store(
            f"[legacy_agent_log] {self.task.name}: {status} - {message}",
            {"type": "legacy_agent_execution", "agent_id": self.task.id, "success": success}
        )
        
        if success:
            self.task.success_count += 1
        else:
            self.task.error_count += 1
        
        self.task.last_run = timestamp
        
        os.makedirs("agent_logs", exist_ok=True)
        log_file = f"agent_logs/legacy_{self.task.id}_{datetime.now().strftime('%Y%m')}.log"
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"{json.dumps(log_entry, ensure_ascii=False)}\n")

class RSSMonitorAgent(BaseAgent):
    """Агент мониторинга RSS и публикации контента (устаревший)"""
    
    def execute(self) -> bool:
        try:
            import feedparser
            
            rss_url = self.task.config.get("rss_url", "")
            chat_id = self.task.config.get("chat_id", "")
            style = self.task.config.get("style", "информативный стиль")
            max_posts = self.task.config.get("max_posts", 3)
            
            if not rss_url or not chat_id:
                self.log_execution(False, "Отсутствуют обязательные параметры")
                return False
            
            # Получаем RSS
            feed = feedparser.parse(rss_url)
            if not feed.entries:
                self.log_execution(False, "RSS лента пуста или недоступна")
                return False
            
            # Обрабатываем посты
            processed_posts = 0
            for entry in feed.entries[:max_posts]:
                try:
                    title = entry.get('title', 'Без заголовка')
                    link = entry.get('link', '')
                    description = entry.get('description', '')
                    
                    # Генерируем контент через LLM
                    prompt = f"Перепиши новость в стиле '{style}':\n\nЗаголовок: {title}\nОписание: {description}\nСсылка: {link}"
                    generated_content = ask_llm_with_context(prompt)
                    
                    # Отправляем в Telegram
                    message = f"{generated_content}\n\n🔗 {link}"
                    send_telegram_message(chat_id, message)
                    
                    processed_posts += 1
                    time.sleep(2)  # Пауза между постами
                    
                except Exception as e:
                    self.logger.error(f"Ошибка обработки поста: {e}")
                    continue
            
            self.log_execution(True, f"Обработано {processed_posts} постов")
            return True
            
        except ImportError:
            self.log_execution(False, "Модуль feedparser не установлен")
            return False
        except Exception as e:
            self.log_execution(False, f"Ошибка выполнения: {str(e)}")
            return False

class ContentGeneratorAgent(BaseAgent):
    """Агент генерации контента (устаревший)"""
    
    def execute(self) -> bool:
        try:
            template_id = self.task.config.get("template_id", "")
            chat_id = self.task.config.get("chat_id", "")
            topics = self.task.config.get("topics", [])
            
            if not template_id or not chat_id:
                self.log_execution(False, "Отсутствуют обязательные параметры")
                return False
            
            # Выбираем случайную тему
            import random
            topic = random.choice(topics) if topics else "общая тема"
            
            # Генерируем контент
            context = {"topic": topic, "timestamp": datetime.now().isoformat()}
            content = generate_from_template(template_id, context)
            
            # Отправляем в Telegram
            send_telegram_message(chat_id, content)
            
            self.log_execution(True, f"Сгенерирован контент по теме: {topic}")
            return True
            
        except Exception as e:
            self.log_execution(False, f"Ошибка генерации контента: {str(e)}")
            return False

class LegacyAgentManager:
    """Менеджер устаревших автономных агентов"""
    
    def __init__(self, memory: MemoryCore = None):
        self.memory = memory or MemoryCore()
        self.agents: Dict[str, BaseAgent] = {}
        self.scheduler_thread = None
        self.scheduler_running = False
        
        logger.warning("Используется устаревший LegacyAgentManager. "
                      "Рекомендуется использовать AgentManager из agents_v2.py")
    
    def add_agent(self, agent: BaseAgent):
        """Добавляет агента в менеджер"""
        self.agents[agent.task.id] = agent
        self._schedule_agent(agent)
        logger.info(f"Устаревший агент {agent.task.name} добавлен в менеджер")
    
    def _schedule_agent(self, agent: BaseAgent):
        """Настраивает планировщик для агента"""
        pattern = agent.task.schedule_pattern
        
        # Простая обработка расписания
        if pattern == "0 9,15,20 * * *":
            schedule.every().day.at("09:00").do(self._execute_agent, agent.task.id)
            schedule.every().day.at("15:00").do(self._execute_agent, agent.task.id)
            schedule.every().day.at("20:00").do(self._execute_agent, agent.task.id)
        elif "every" in pattern and "hours" in pattern:
            hours = int(pattern.split()[1])
            schedule.every(hours).hours.do(self._execute_agent, agent.task.id)
    
    def _execute_agent(self, agent_id: str):
        """Выполняет агента"""
        if agent_id in self.agents:
            agent = self.agents[agent_id]
            try:
                agent.execute()
            except Exception as e:
                logger.error(f"Ошибка выполнения устаревшего агента {agent_id}: {e}")
    
    def start_scheduler(self):
        """Запускает планировщик"""
        if self.scheduler_running:
            return
        
        self.scheduler_running = True
        
        def scheduler_loop():
            while self.scheduler_running:
                try:
                    schedule.run_pending()
                    time.sleep(1)
                except Exception as e:
                    logger.error(f"Ошибка планировщика устаревших агентов: {e}")
        
        self.scheduler_thread = threading.Thread(target=scheduler_loop, daemon=True)
        self.scheduler_thread.start()
        
        logger.info("Планировщик устаревших агентов запущен")
    
    def stop_scheduler(self):
        """Останавливает планировщик"""
        self.scheduler_running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        logger.info("Планировщик устаревших агентов остановлен")

# Глобальный менеджер для обратной совместимости
_legacy_manager = None

def get_agent_manager() -> LegacyAgentManager:
    """Возвращает устаревший менеджер агентов (для совместимости)"""
    global _legacy_manager
    if _legacy_manager is None:
        _legacy_manager = LegacyAgentManager()
        logger.warning("Создан устаревший менеджер агентов. "
                      "Используйте get_agent_manager() из agents_v2.py для новой архитектуры")
    return _legacy_manager

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
    Создает устаревшего автономного агента (для обратной совместимости)
    
    ВНИМАНИЕ: Эта функция устарела. Используйте AgentManager из agents_v2.py
    """
    logger.warning("Функция create_autonomous_agent_from_plan устарела. "
                  "Используйте create_rss_agent() из agents_v2.AgentManager")
    
    # Создаем задачу
    task = AgentTask(
        id=f"{agent_type}_{int(time.time())}",
        name=name,
        description=f"Устаревший {agent_type} агент",
        schedule_pattern=schedule,
        task_type=agent_type,
        config={
            "rss_url": rss_url,
            "chat_id": chat_id,
            "style": style,
            **kwargs
        },
        created_at=datetime.now().isoformat()
    )
    
    # Создаем агента
    if agent_type == "rss_monitor":
        agent = RSSMonitorAgent(task, memory)
    elif agent_type == "content_generator":
        agent = ContentGeneratorAgent(task, memory)
    else:
        raise ValueError(f"Неизвестный тип агента: {agent_type}")
    
    # Добавляем в менеджер
    manager = get_agent_manager()
    manager.add_agent(agent)
    
    # Запускаем планировщик если не запущен
    if not manager.scheduler_running:
        manager.start_scheduler()
    
    # Сохраняем конфигурацию
    os.makedirs("approved_goals", exist_ok=True)
    config_file = f"approved_goals/legacy_agent_{task.id}.json"
    
    with open(config_file, "w", encoding="utf-8") as f:
        json.dump(asdict(task), f, indent=2, ensure_ascii=False)
    
    logger.info(f"Устаревший агент {name} создан с ID {task.id}")
    return task.id

# Предупреждение при импорте модуля
logger.warning("Модуль autonomous_agents_legacy.py устарел. "
              "Используйте agents_v2.py для новой архитектуры агентов.")