# intuition_advanced.py — Голос Интуиции (расширенный режим "полное пробуждение")
import logging
from datetime import datetime
from typing import List, Dict, Optional

import numpy as np

from memory_core import MemoryCore

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class IntuitionEngine:
    """
    Расширенная интуиция:
      - отслеживает недавние ошибки по похожим запросам
      - ищет старые похожие кейсы и напоминает о них
      - проверяет возможный конфликт с активными целями (низкая семантическая близость)
    Использует ОДИН embedder из MemoryCore (без повторной загрузки модели).
    """
    def __init__(self, threshold_days: int = 7, conflict_similarity_threshold: float = 0.40):
        self.memory = MemoryCore()
        self.embedder = self.memory.embedder  # не грузим модель второй раз
        self.threshold_days = threshold_days
        self.conflict_similarity_threshold = conflict_similarity_threshold
        self.warning_markers = ["ошибка", "не удалось", "сбой", "падение"]

    # === Публичный API ===
    def detect_intuition(self, user_input: str) -> Optional[str]:
        try:
            hints: List[str] = []

            recent_err = self._find_recent_errors(user_input)
            if recent_err:
                hints.append("❗ Интуиция: с похожим запросом недавно были проблемы. Проверь альтернативу или шаги безопасности.")

            old_sim = self._find_old_similar(user_input)
            if old_sim:
                hints.append("💭 Похоже, это уже поднималось раньше. Возможно, есть невидимые риски или забытые детали.")

            conflicts = self._find_conflicting_goals(user_input)
            if conflicts:
                hints.append("⚠️ Возможен конфликт с текущими целями. Уточни приоритеты или переформулируй задачу.")

            return "\\n".join(hints) if hints else None
        except Exception as e:
            logger.warning(f"⚠️ Интуиция недоступна: {e}")
            return None

    # === Внутренние методы ===
    def _find_recent_errors(self, query: str) -> List[Dict]:
        """Ищем в памяти ответы/события, где были явные ошибки по похожей теме (последние ~N штук)"""
        results = self.memory.get_similar(query, n_results=6, filter_type="response")
        out = []
        for r in results:
            text = (r.get("content") or "").lower()
            if any(mark in text for mark in self.warning_markers):
                out.append(r)
        return out

    def _find_old_similar(self, query: str) -> List[Dict]:
        """Находим похожие записи старше threshold_days (напоминание об опыте)"""
        matches = self.memory.get_similar(query, n_results=6)
        old = []
        for m in matches:
            ts = None
            meta = m.get("metadata") or {}
            if isinstance(meta, dict):
                ts_str = meta.get("timestamp")
                if ts_str:
                    try:
                        ts = datetime.fromisoformat(ts_str)
                    except Exception:
                        ts = None
            if ts:
                if (datetime.now() - ts).days > self.threshold_days:
                    old.append(m)
        return old

    def _find_conflicting_goals(self, query: str) -> List[Dict]:
        """Проверяем активные цели на возможный семантический конфликт с запросом"""
        goals = self.memory.get_similar("goal", filter_type="goal", n_results=8)
        if not goals:
            return []

        q_vec = self.embedder.encode(query)
        conflicts = []
        for g in goals:
            gtxt = g.get("content") or ""
            g_vec = self.embedder.encode(gtxt)
            sim = self._cosine_sim(q_vec, g_vec)
            if sim < self.conflict_similarity_threshold:
                conflicts.append({"goal": gtxt, "similarity": float(sim)})
        return conflicts

    @staticmethod
    def _cosine_sim(a, b) -> float:
        a = np.asarray(a, dtype=float)
        b = np.asarray(b, dtype=float)
        denom = (np.linalg.norm(a) * np.linalg.norm(b)) or 1e-8
        return float(np.dot(a, b) / denom)
