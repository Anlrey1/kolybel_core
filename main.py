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
from agents import start_autonomous_system, stop_autonomous_system, get_agents_status

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

memory = MemoryCore()

# Загрузка манифеста в память (если есть)


def load_manifest_to_memory(mem: MemoryCore):
    try:
        if os.path.isfile("kolybel_manifest.txt"):
            with open("kolybel_manifest.txt", "r", encoding="utf-8") as f:
                txt = f.read()
                mem.store(f"[manifest] {txt}", {
                          "type": "system", "source": "manual"})
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
for p in ["approved_goals", "agent_logs", "models_cache", "training_workflows", "logs", "goals", "autonomous_agents"]:
    os.makedirs(p, exist_ok=True)

# Запуск автономной системы агентов
print("🚀 Запуск автономной системы агентов...")
start_autonomous_system(memory)

try:
    train_from_examples()
    print("🎓 Автообучение завершено.")
except Exception as e:
    print(f"⚠️ Ошибка автообучения: {e}")

# Команды


def recognize_command(token: str) -> str:
    commands = {
        "выход": "выход", "exit": "выход", "quit": "выход", "пока": "выход",
        "clear": "clear", "cls": "clear", "очистить": "clear",
        "make-dirs": "make-dirs", "создать-папки": "make-dirs",
        "agents": "agents", "агенты": "agents",
        "start-agents": "start-agents", "запустить-агентов": "start-agents",
        "stop-agents": "stop-agents", "остановить-агентов": "stop-agents",
    }
    return commands.get(token.lower(), "unknown")


def format_response(s: str) -> str:
    if not s:
        return "🤔 Пустой ответ."
    return s


def clear_terminal():
    os.system("cls" if os.name == "nt" else "clear")


print("🌟 Колыбель готова к работе!")
print("💡 Доступные команды:")
print("   • agents - статус агентов")
print("   • start-agents - запуск автономной системы")
print("   • stop-agents - остановка автономной системы")
print("   • goal: <текст> - сохранить цель")
print("   • remind - напомнить цели")
print("   • audit - аудит агентов")
print("   • stats - статистика")
print("   • clear - очистить экран")
print("   • exit - выход")
print()

while True:
    try:
        user_input = input("🔹 Колыбели: ").strip()
        if not user_input:
            continue

        token = user_input.split()[0]
        command = recognize_command(token)

        if command in ["выход", "exit", "quit", "пока"]:
            print("🚪 Выход из Сессии Колыбели...")
            print("⏹️ Остановка автономной системы...")
            stop_autonomous_system(memory)
            with open(AWAKENING_LOG_FILE, "a", encoding="utf-8") as logf:
                logf.write(
                    f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 🚪 Выход из сессии\n")
            break

        if command == "clear":
            clear_terminal()
            continue

        if command == "make-dirs":
            for p in ["approved_goals", "agent_logs", "models_cache", "training_workflows", "logs", "goals", "autonomous_agents"]:
                os.makedirs(p, exist_ok=True)
            print("📁 Папки подготовлены.")
            continue

        if command == "agents":
            status = get_agents_status(memory)
            print("🤖 Статус агентов:")
            print(f"   • Всего агентов: {status['total_agents']}")
            print(f"   • Автономных: {status['autonomous_count']}")
            print(f"   • N8N: {status['n8n_count']}")
            print(
                f"   • Планировщик: {'🟢 РАБОТАЕТ' if status['scheduler_running'] else '🔴 ОСТАНОВЛЕН'}")

            if status['autonomous_agents']:
                print("\n📋 Автономные агенты:")
                for agent in status['autonomous_agents']:
                    status_icon = "🟢" if agent.get('is_active') else "🔴"
                    success_rate = agent.get('success_rate', 0)
                    print(
                        f"   {status_icon} {agent['name']} ({agent['type']}) - {success_rate:.1f}% успешность")
            continue

        if command == "start-agents":
            start_autonomous_system(memory)
            print("🚀 Автономная система агентов запущена")
            continue

        if command == "stop-agents":
            stop_autonomous_system(memory)
            print("⏹️ Автономная система агентов остановлена")
            continue

        # Автошаблоны
        if should_use_template(user_input):
            logger.info(f"🔍 Автоподбор шаблона для: '{user_input}'")
            tid = pick_template_id(user_input)
            reply = generate_from_template(
                tid, context={"topic": user_input}, use_training=True)
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
        print("⏹️ Остановка автономной системы...")
        stop_autonomous_system(memory)
        break
    except Exception as e:
        print(f"⚠️ Ошибка: {e}")
        logger.exception("Подробности ошибки:")
