# intent.py — маршрутизатор намерений
from typing import Optional
from template_engine import TemplateManager, generate_from_template
from llm import ask_llm_with_context

INTENT_KEYWORDS = ["создай", "сделай", "запусти", "агент", "канал", "пост"]
AGENT_KEYWORDS = ["агент", "бот", "сканер", "разведчик"]
IMAGE_KEYWORDS = ["картинку", "иллюстрацию", "изображение"]

_templates = TemplateManager()

def handle_intent(prompt: str, memory=None) -> str:
    text = prompt.lower()

    # Создание агента (заглушка)
    if any(k in text for k in INTENT_KEYWORDS) and any(k in text for k in AGENT_KEYWORDS):
        if memory:
            memory.store(prompt, {"type": "agent_request"})
        return "[↪️ Агент создаётся...]"

    # Картинка → просим LLM сгенерировать промт (без генерации изображения)
    if any(k in text for k in IMAGE_KEYWORDS):
        return ask_llm_with_context(f"Сгенерируй промт для создания изображения: {prompt}", model="nous-hermes")

    # Иначе — попробуем шаблон
    t = _templates.best(prompt)
    if t:
        return generate_from_template(t.id, context={"topic": prompt}, use_training=True)

    # Фолбэк — прямой LLM
    return ask_llm_with_context(prompt)
