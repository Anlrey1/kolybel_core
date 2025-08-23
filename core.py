# core.py — оркестрация диалога/интентов/шаблонов + Интуиция (баз/расшир)
import logging
from typing import Tuple

from memory_core import MemoryCore
from llm import ask_llm_with_context
from template_engine import TemplateManager, generate_from_template
from intent import handle_intent

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Диалоговая память уровня сессии
DIALOG_HISTORY = []
DIALOG_MEMORY_THRESHOLD = 6
FULL_AWARENESS = True  # ← ВКЛ «полное пробуждение» для расширенной интуиции

memory = MemoryCore()
templates = TemplateManager()

# Интуиция: базовая и расширенная
from intuition import IntuitionEngine as BasicIntuition
try:
    from intuition_advanced import IntuitionEngine as AdvancedIntuition
except Exception:
    AdvancedIntuition = BasicIntuition  # fallback

intuition = AdvancedIntuition() if FULL_AWARENESS else BasicIntuition()

def should_use_template(user_input: str) -> bool:
    t = templates.best(user_input)
    return t is not None

def enhance_with_analytics(text: str, user_input: str) -> str:
    # Заглушка для метрик: можно обогатить хэштегами/CTA
    return text

def log_dialog(q: str, a: str):
    try:
        memory.store(q, {"type": "dialog_q"})
        memory.store(a, {"type": "response", "engagement": 0.7})
    except Exception:
        pass

def handle_system_commands(user_input: str) -> str:
    from goals import save_goal, remind_goals, audit_agents, summarize_agent_performance
    cmd = user_input.strip().lower()

    if cmd.startswith("goal:"):
        text = user_input.split(":", 1)[1].strip()
        save_goal(memory, text)
        return "🎯 Цель сохранена"

    if cmd.startswith("remind"):
        remind_goals()
        return "🔔 Напоминание показано (см. консоль)"

    if cmd.startswith("audit"):
        audit_agents()
        return "🧾 Аудит завершён"

    if cmd.startswith("mission"):
        return "🛰 Миссия зафиксирована (заглушка)"

    if cmd.startswith("stats"):
        return summarize_agent_performance()

    return "❓ Неизвестная системная команда"

def pick_template_id(user_input: str) -> str:
    t = templates.best(user_input)
    return t.id if t else ""

def _maybe_prepend_intuition(user_input: str, reply: str) -> str:
    """Если интуиция что-то подсказала — добавляем предупреждения сверху."""
    try:
        hint = intuition.detect_intuition(user_input)
        if hint:
            return f"{hint}\n\n{reply}"
        return reply
    except Exception:
        return reply

def handle_user_input(user_input: str) -> str:
    # Сначала системные команды
    if user_input.startswith(("goal:", "mission", "remind", "audit", "stats")):
        reply = handle_system_commands(user_input)
        return _maybe_prepend_intuition(user_input, reply)

    # Интенты (агенты/картинки/и т.п.)
    reply = handle_intent(user_input, memory=memory)
    return _maybe_prepend_intuition(user_input, reply)
