# intuition.py — Голос Интуиции (без тяжёлых зависимостей)
import logging
from typing import Optional
from memory_core import MemoryCore

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class IntuitionEngine:
    def __init__(self):
        self.memory = MemoryCore()

    def detect_intuition(self, user_input: str) -> Optional[str]:
        try:
            # Простая эвристика: если похожие ошибки встречались — предупреждаем
            candidates = self.memory.get_similar(user_input, n_results=3)
            texts = [c["content"].lower() for c in candidates]
            if any("ошибка" in t or "не удалось" in t for t in texts):
                return "❗ Интуиция: похоже, раньше с этим были проблемы. Проверь альтернативу."
            return None
        except Exception as e:
            logger.warning(f"Интуиция недоступна: {e}")
            return None
