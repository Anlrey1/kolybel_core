# template_engine.py — единый движок шаблонов + TemplateManager с порогом схожести
import logging
from typing import Dict, Optional, List
import numpy as np

from prompt_templates_loader import load_prompt_templates, Template
from llm import ask_llm_with_context  # только LLM-вызов

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

_SIM_THRESHOLD = 0.65  # порог для автоподбора; ниже — не использовать шаблон

class TemplateManager:
    def __init__(self):
        from sentence_transformers import SentenceTransformer
        self.templates: List[Template] = load_prompt_templates()
        self.embedder = SentenceTransformer("all-MiniLM-L6-v2")

    def _similarity(self, a, b) -> float:
        a = np.asarray(a, dtype=float); b = np.asarray(b, dtype=float)
        denom = (np.linalg.norm(a) * np.linalg.norm(b)) or 1e-8
        return float(np.dot(a, b) / denom)

    def best(self, query: str) -> Optional[Template]:
        if not self.templates:
            return None
        qv = self.embedder.encode(query)
        best_tpl, best_sim = None, -1.0
        for t in self.templates:
            tv = self.embedder.encode(f"{t.title} {t.description} {' '.join(t.tags)}")
            sim = self._similarity(qv, tv)
            if sim > best_sim:
                best_sim, best_tpl = sim, t
        # применяем порог; если не дотягивает — шаблон не используем
        if best_sim >= _SIM_THRESHOLD:
            logger.info(f"[TemplateManager] подобран шаблон '{best_tpl.id}' (sim={best_sim:.2f})")
            return best_tpl
        logger.info(f"[TemplateManager] релевантный шаблон не найден (max sim={best_sim:.2f} < {_SIM_THRESHOLD})")
        return None

def generate_from_template(template_id: str, context: Optional[Dict] = None, use_training: bool = True) -> str:
    try:
        templates = load_prompt_templates()
        t = next((x for x in templates if x.id == template_id), None)
        if not t:
            return f"❌ Шаблон '{template_id}' не найден"

        content = t.content
        if context:
            for k, v in context.items():
                content = content.replace(f"{{{{{k}}}}}", str(v))

        training = ""
        if use_training:
            try:
                with open("training_workflows/agent_prompt_examples.txt", "r", encoding="utf-8") as f:
                    training = f.read()
            except FileNotFoundError:
                logger.info("Нет обучающих примеров — используем базовый шаблон")

        prompt = f"""Ты — ИИ-ассистент, говорящий на русском.
Применяй лучшие практики из примеров к новому запросу.
ОТВЕЧАЙ ТОЛЬКО НА РУССКОМ ЯЗЫКЕ.

ШАБЛОН:
{content}

ПРИМЕРЫ ЛУЧШИХ ОТВЕТОВ:
{training}
"""
        reply = ask_llm_with_context(prompt)
        return reply.strip() or content
    except Exception as e:
        logger.error(f"Ошибка генерации по шаблону: {e}")
        return "⚠️ Не удалось применить шаблон"
