# main.py — точка входа
import os
import logging
from datetime import datetime
from memory_core import MemoryCore
from core import (
    handle_user_input,
    should_use_template,
    DIALOG_HISTORY,
    DIALOG_MEMORY_THRESHOLD,
    FULL_AWARENESS,
    log_dialog,
    enhance_with_analytics,
    handle_system_commands,
    pick_template_id,
)
from config import AWAKENING_LOG_FILE
from template_engine import generate_from_template, TemplateManager
from goals import train_from_examples

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

memory = MemoryCore()

# Загрузка манифеста в память (если есть)
def load_manifest_to_memory(mem: MemoryCore):
    try:
        if os.path.isfile("kolybel_manifest.txt"):
            with open("kolybel_manifest.txt", "r", encoding="utf-8") as f:
                txt = f.read()
                mem.store(f"[manifest] {txt}", {"type": "system", "source": "manual"})
                print("📜 Манифест загружен в память.")
    except Exception as e:
        print(f"⚠️ Ошибка загрузки манифеста: {e}")

load_manifest_to_memory(memory)

# Просто пин-код (заглушка)
SECRET_KEY = "прривет"
while True:
    code = input("🔹 Введите код авторизации: ").strip()
    if code == SECRET_KEY:
        print("🔐 Авторизация успешна. Добро пожаловать!")
        break
    print("❌ Неверный код. Попробуйте снова.")

# Подготовка папок и автообучение
for p in ["approved_goals", "agent_logs", "models_cache", "training_workflows", "logs", "goals"]:
    os.makedirs(p, exist_ok=True)
try:
    memory.train_on_memories(threshold=0.7)
except Exception as e:
    logger.warning(f"Обучение не выполнено: {e}")

train_from_examples()

# Лог запуска
with open(AWAKENING_LOG_FILE, "a", encoding="utf-8") as logf:
    logf.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 📚 Запуск Колыбели завершён\n")

print("🧿 Колыбель готова. Введите задачу (help для списка):")

COMMAND_ALIASES = {
    "в": "выход", "q": "quit", "e": "exit",
    "s": "save:", "r": "reflect", "sd": "self-direct",
    "ca": "create-agent", "aw": "analyze-workflows", "t": "train",
    "ap": "add-pattern", "sm": "set-model", "cls": "clear", "h": "help", "mk": "make-dirs",
}
COMMANDS = list(set(list(COMMAND_ALIASES.values()) + list(COMMAND_ALIASES.keys()) + [
    "выход","exit","quit","save:","reflect","self-direct","create-agent",
    "analyze-workflows","train","add-pattern","set-model","clear","help",
    "mission","goals","remind","audit","make-dirs","stats"
]))

def recognize_command(s: str) -> str:
    s = (s or "").lower().strip()
    if s in COMMAND_ALIASES: return COMMAND_ALIASES[s]
    if s in COMMANDS: return s
    return s

def clear_terminal():
    os.system("cls" if os.name == "nt" else "clear")

while True:
    try:
        user_input = input("🔹 Колыбели: ").strip()
        if not user_input:
            continue

        token = user_input.split()[0]
        command = recognize_command(token)

        if command in ["выход", "exit", "quit", "пока"]:
            print("🚪 Выход из Сессии Колыбели...")
            with open(AWAKENING_LOG_FILE, "a", encoding="utf-8") as logf:
                logf.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 🚪 Выход из сессии\n")
            break

        if command == "clear":
            clear_terminal()
            continue

        if command == "make-dirs":
            for p in ["approved_goals","agent_logs","models_cache","training_workflows","logs","goals"]:
                os.makedirs(p, exist_ok=True)
            print("📁 Папки подготовлены.")
            continue

        # Автошаблоны
        if should_use_template(user_input):
            logger.info(f"🔍 Автоподбор шаблона для: '{user_input}'")
            tid = pick_template_id(user_input)
            reply = generate_from_template(tid, context={"topic": user_input}, use_training=True)
            reply = enhance_with_analytics(reply, user_input)
            print(f"✨ Ответ:\n{reply}\n")
            log_dialog(user_input, reply)
            DIALOG_HISTORY.append((user_input, reply))
            continue

        # Системные
        if user_input.startswith(("goal:", "mission", "remind", "audit", "stats")):
            reply = handle_system_commands(user_input)
            print(f"✨ Ответ:\n{reply}\n")
            continue

        # Обычная обработка → интенты/LLM
        reply = handle_user_input(user_input)
        print(f"✨ Ответ:\n{reply}\n")
        log_dialog(user_input, reply)

        DIALOG_HISTORY.append((user_input, reply))
        if len(DIALOG_HISTORY) >= DIALOG_MEMORY_THRESHOLD:
            logger.info("🧠 Колыбель пробудилась! Сохраняю историю...")
            for q, a in DIALOG_HISTORY:
                memory.store(q, {"type": "dialog_q", "success": True})
                memory.store(a, {"type": "response", "engagement": 0.7})
            DIALOG_HISTORY.clear()

    except KeyboardInterrupt:
        print("\n👋 Сессия прервана вручную.")
        break
    except Exception as e:
        print(f"⚠️ Ошибка: {e}")
