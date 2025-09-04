# agents_v2.py — новая система агентов с независимой архитектурой
import logging
import os
import json
import schedule
from typing import Dict, List, Optional, Any
from datetime import datetime

# Заглушки для отсутствующих модулей
try:
    from memory_core import MemoryCore
except ImportError:
    class MemoryCore:
        def store(self, content, metadata=None):
            print(f"[MEMORY] {content}")

        def get_similar(self, query, n_results=5):
            return []

from agent_specification import AgentSpecification, AgentSpecificationFactory
from runtime_orchestrator import RuntimeOrchestrator, ExecutionPolicy
from runtime_adapters import ExecutionResult
from config import LOG_DIR

# === Новая интеграция знаний по n8n ===
try:
    from n8n_docs import N8nKnowledge
except Exception:
    N8nKnowledge = None

logger = logging.getLogger(__name__)

class AgentManager:
    """Менеджер агентов с поддержкой независимой архитектуры"""

    def __init__(self, memory: MemoryCore = None, config: Dict[str, Any] = None):
        self.memory = memory or MemoryCore()
        self.config = config or {}

        # Инициализируем оркестратор
        orchestrator_config = {
            'execution_policy': self.config.get('execution_policy', 'failover'),
            'health_check_interval': self.config.get('health_check_interval', 60),
            'n8n': {
                'api_url': os.getenv('N8N_API_URL', ''),
                'username': os.getenv('N8N_USER', ''),
                'password': os.getenv('N8N_PASSWORD', '')
            },
            'docker': {
                'enabled': self.config.get('docker_enabled', True)
            },
            'local': {
                'max_concurrent': self.config.get('max_concurrent_local', 5)
            }
        }

        self.orchestrator = RuntimeOrchestrator(self.memory, orchestrator_config)

        # Подключаем базу знаний n8n, если доступна
        self.n8n_knowledge = N8nKnowledge(self.memory) if N8nKnowledge else None

        # Регулярное обновление индекса n8n (раз в месяц)
        self._schedule_monthly_n8n_docs_update()

        # Запускаем планировщик
        self.orchestrator.start_scheduler()

        logger.info("Менеджер агентов v2 инициализирован")

    def list_agents(self) -> List[Dict[str, Any]]:
        """Возвращает список всех агентов в системе"""
        # Пока возвращаем пустой список, так как у нас нет хранилища агентов
        # В будущем можно добавить хранение агентов в базе данных
        return []

    def search_n8n_docs(self, query: str, k: int = 8) -> List[Dict[str, Any]]:
        """Поиск по официальной документации n8n (если индекс создан)."""
        if not self.n8n_knowledge:
            logger.warning("N8nKnowledge недоступен. Убедитесь, что модуль n8n_docs присутствует.")
            return []
        return self.n8n_knowledge.search(query, n_results=k)

    def update_n8n_docs_index(self, limit_files: Optional[int] = None) -> Dict[str, Any]:
        """Скачать и проиндексировать официальную документацию n8n."""
        if not self.n8n_knowledge:
            logger.warning("N8nKnowledge недоступен. Убедитесь, что модуль n8n_docs присутствует.")
            return {"status": "error", "reason": "n8n_knowledge_unavailable"}
        stats = self.n8n_knowledge.update_index(limit_files=limit_files)
        # Лог в память
        self.memory.store(
            f"[n8n_docs_update] Индекс обновлён: files={stats.get('files')} chunks={stats.get('chunks')}",
            {"type": "n8n_docs_update", "timestamp": datetime.now().isoformat(), **stats}
        )
        return stats

    def build_n8n_context(self, user_query: str, k: int = 6) -> str:
        """Готовит компактный контекст из n8n-доков для подмешивания в промпт."""
        hits = self.search_n8n_docs(user_query, k=k)
        if not hits:
            return ""
        blocks = []
        for h in hits:
            meta = h.get("metadata", {})
            src = meta.get("url") or meta.get("source_file")
            snippet = h.get("snippet") or h.get("content", "")[:500]
            blocks.append(f"Источник: {src}\n{snippet}")
        return "\n\n".join(blocks)

    # ===== Планировщик месячного обновления n8n-документации =====
    def _schedule_monthly_n8n_docs_update(self):
        if not self.n8n_knowledge:
            return
        state_path = os.path.join(LOG_DIR, "n8n_docs_update_state.json")

        def _read_state() -> dict:
            try:
                with open(state_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}

        def _write_state(state: dict):
            try:
                with open(state_path, "w", encoding="utf-8") as f:
                    json.dump(state, f, ensure_ascii=False, indent=2)
            except Exception as e:
                logger.warning(f"Не удалось записать состояние планировщика: {e}")

        def _job():
            now = datetime.now()
            ym = f"{now.year:04d}-{now.month:02d}"
            st = _read_state()
            if st.get("last_run_month") == ym:
                return  # уже выполняли в этом месяце
            try:
                stats = self.update_n8n_docs_index()
                st["last_run_month"] = ym
                st["last_run_at"] = now.isoformat()
                st["last_stats"] = stats
                _write_state(st)
                logger.info("Ежемесячное обновление n8n-документации завершено")
            except Exception as e:
                logger.error(f"Ежемесячное обновление n8n-документации завершилось ошибкой: {e}")

        # Раз в день в 03:30 проверяем, выполняли ли в этом месяце
        schedule.every().day.at("03:30").do(_job)

    # ===== Еженедельное самообучение на успешных примерах =====
    def _schedule_self_training(self):
        def _job():
            try:
                self.memory.train_on_memories(threshold=0.7)
                self.memory.store(
                    "[self_training] Обучение завершено",
                    {"type": "self_training", "timestamp": datetime.now().isoformat()}
                )
                logger.info("Еженедельное самообучение завершено")
            except Exception as e:
                logger.error(f"Ошибка самообучения: {e}")
        # Каждое воскресенье в 04:15
        schedule.every().sunday.at("04:15").do(_job)

# ... existing code ...