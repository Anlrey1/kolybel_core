# goals.py — цели/обучение/аудит
import os
from datetime import datetime
import logging
from memory_core import MemoryCore

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def save_goal(memory: MemoryCore, goal_text: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    line = f"[ ] {ts} — {goal_text}"
    memory.store(f"[goal] {goal_text}", {"type": "goal", "timestamp": datetime.now().isoformat()})
    os.makedirs("approved_goals", exist_ok=True)
    with open("goals.log", "a", encoding="utf-8") as f:
        f.write(f"{line}\n")
    with open(f"approved_goals/goal_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt", "w", encoding="utf-8") as g:
        g.write(line)

def audit_agents():
    path = "approved_goals"
    print("🔍 Аудит целей/агентов:")
    if not os.path.isdir(path):
        print("(папка отсутствует)")
        return
    for name in os.listdir(path):
        if name.endswith(".txt"):
            print("•", name)

def remind_goals():
    print("🔔 Напоминание о целях:")
    try:
        with open("goals.log", "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("[ ]"):
                    print("⏳", line.strip())
    except FileNotFoundError:
        print("(нет активных целей)")

def train_from_examples():
    try:
        mem = MemoryCore()
        examples_dir = "training_workflows"
        os.makedirs(examples_dir, exist_ok=True)
        count = 0
        for filename in os.listdir(examples_dir):
            fp = os.path.join(examples_dir, filename)
            if os.path.isfile(fp):
                with open(fp, "r", encoding="utf-8") as f:
                    content = f.read()
                    mem.store(f"[training] {filename}: {content[:120]}...", {"type": "training"})
                    count += 1
        with open("logs/awakening.log", "a", encoding="utf-8") as log:
            log.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 🎓 Загрузка примеров ({count})\n")
    except Exception as e:
        logger.warning(f"Ошибка обучения: {e}")

def summarize_agent_performance():
    # Заглушка: вернём простые цифры
    return "📈 Статистика агентов: активные 0/0, успешность 0%"
