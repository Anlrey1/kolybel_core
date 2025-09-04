#!/usr/bin/env python3
# start_web_interface.py — запуск веб-интерфейса Колыбели

import os
import sys
import logging
from datetime import datetime

# Добавляем текущую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from web_interface import app
from memory_core import MemoryCore
from agents import start_autonomous_system

def setup_logging():
    """Настройка логирования"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/web_interface.log'),
            logging.StreamHandler()
        ]
    )

def check_dependencies():
    """Проверка зависимостей"""
    required_dirs = [
        'templates', 'static', 'static/css', 'static/js',
        'logs', 'autonomous_agents', 'agent_logs'
    ]
    
    for dir_name in required_dirs:
        if not os.path.exists(dir_name):
            os.makedirs(dir_name, exist_ok=True)
            print(f"📁 Создана папка: {dir_name}")

def initialize_system():
    """Инициализация системы"""
    print("🔧 Инициализация системы Колыбели...")
    
    # Инициализируем память
    memory = MemoryCore()
    
    # Загружаем манифест
    if os.path.exists("kolybel_manifest.txt"):
        with open("kolybel_manifest.txt", "r", encoding="utf-8") as f:
            manifest = f.read()
            memory.store(f"[manifest] {manifest}", {"type": "system", "source": "manual"})
        print("📜 Манифест загружен в память")
    
    # Запускаем автономную систему агентов
    try:
        start_autonomous_system(memory)
        print("🤖 Автономная система агентов запущена")
    except Exception as e:
        print(f"⚠️ Ошибка запуска агентов: {e}")
    
    return memory

def main():
    """Основная функция"""
    print("🌟 Запуск веб-интерфейса Колыбели")
    print("=" * 50)
    
    # Настройка логирования
    setup_logging()
    
    # Проверка зависимостей
    check_dependencies()
    
    # Инициализация системы
    memory = initialize_system()
    
    # Информация о запуске
    print("\n🚀 Веб-интерфейс готов к запуску!")
    print(f"📅 Время запуска: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌐 Адрес: http://localhost:5000")
    print(f"💬 Чат: http://localhost:5000/chat")
    print(f"🤖 Агенты: http://localhost:5000/agents")
    print(f"🎯 Цели: http://localhost:5000/goals")
    print(f"📊 Аналитика: http://localhost:5000/analytics")
    print(f"⚙️ Настройки: http://localhost:5000/settings")
    print("\n💡 Горячие клавиши:")
    print("   • Ctrl+K - быстрые команды")
    print("   • Escape - закрыть модальные окна")
    print("\n🛑 Для остановки нажмите Ctrl+C")
    print("=" * 50)
    
    try:
        # Запуск веб-сервера
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=False  # Отключаем debug в продакшене
        )
    except KeyboardInterrupt:
        print("\n\n🛑 Получен сигнал остановки...")
        print("⏹️ Остановка автономной системы агентов...")

        try:
            from agents import stop_autonomous_system
            stop_autonomous_system(memory)
            print("✅ Автономная система остановлена")
        except Exception as e:
            print(f"⚠️ Ошибка остановки агентов: {e}")

        print("👋 Веб-интерфейс Колыбели остановлен")
        print("🙏 Спасибо за использование!")

    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        logging.exception("Критическая ошибка веб-интерфейса")
        sys.exit(1)

if __name__ == "__main__":
    main()