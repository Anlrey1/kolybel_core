#!/usr/bin/env python3
# start_kolybel.py — скрипт запуска Колыбель v2

import os
import sys
import subprocess
import logging
from pathlib import Path

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_dependencies():
    """Проверяет наличие необходимых зависимостей"""
    required_packages = [
        'flask',
        'schedule',
        'feedparser'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("❌ Отсутствуют необходимые пакеты:")
        for package in missing_packages:
            print(f"   • {package}")
        
        print("\n📦 Установите недостающие пакеты:")
        print(f"pip install {' '.join(missing_packages)}")
        
        install = input("\n🤔 Установить автоматически? (y/n): ").lower().strip()
        if install in ['y', 'yes', 'да']:
            try:
                subprocess.check_call([sys.executable, '-m', 'pip', 'install'] + missing_packages)
                print("✅ Пакеты установлены успешно!")
            except subprocess.CalledProcessError as e:
                print(f"❌ Ошибка установки пакетов: {e}")
                return False
        else:
            return False
    
    return True

def create_directories():
    """Создает необходимые директории"""
    directories = [
        'agent_logs',
        'approved_goals',
        'templates',
        'static'
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
    
    logger.info("Директории созданы")

def show_banner():
    """Показывает баннер приложения"""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║    🤖 Колыбель v2 - Автономный Интеллектуальный Ассистент    ║
║                                                              ║
║    Независимая архитектура агентов с автоматическим failover ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
"""
    print(banner)

def show_menu():
    """Показывает главное меню"""
    print("\n🎯 Выберите действие:")
    print("1. 🌐 Запустить веб-интерфейс")
    print("2. 🔄 Запустить миграцию агентов")
    print("3. 🤖 Создать тестового агента")
    print("4. 📊 Показать статус системы")
    print("5. 🧪 Запустить тесты")
    print("0. 🚪 Выход")
    
    return input("\n👉 Ваш выбор: ").strip()

def start_web_interface():
    """Запускает веб-интерфейс"""
    try:
        from web_interface import main as web_main
        web_main()
    except ImportError as e:
        logger.error(f"Ошибка импорта веб-интерфейса: {e}")
        print("❌ Не удалось запустить веб-интерфейс")
    except Exception as e:
        logger.error(f"Ошибка запуска веб-интерфейса: {e}")
        print(f"❌ Ошибка: {e}")

def run_migration():
    """Запускает миграцию агентов"""
    try:
        from migration_tool import main as migration_main
        migration_main()
    except ImportError as e:
        logger.error(f"Ошибка импорта инструмента миграции: {e}")
        print("❌ Не удалось запустить миграцию")
    except Exception as e:
        logger.error(f"Ошибка миграции: {e}")
        print(f"❌ Ошибка миграции: {e}")

def create_test_agent():
    """Создает тестового агента"""
    try:
        from agents_v2 import get_agent_manager
        
        manager = get_agent_manager()
        
        print("\n🧪 Создание тестового RSS агента...")
        
        agent_id = manager.create_rss_agent(
            name="Тестовый DTF агент",
            owner="test_user",
            rss_url="https://dtf.ru/rss",
            telegram_chat_id="-1002669388680",
            schedule="*/30 * * * *",  # Каждые 30 минут
            style="краткий информативный стиль",
            runtime_preferences=["local", "n8n"]
        )
        
        print(f"✅ Тестовый агент создан с ID: {agent_id}")
        
        # Пробуем выполнить агента
        print("🚀 Пробное выполнение агента...")
        result = manager.execute_agent(agent_id)
        
        print(f"📊 Результат выполнения:")
        print(f"   Статус: {result.status.value}")
        print(f"   Сообщение: {result.message}")
        print(f"   Время выполнения: {result.execution_time:.2f}с")
        
    except Exception as e:
        logger.error(f"Ошибка создания тестового агента: {e}")
        print(f"❌ Ошибка: {e}")

def show_system_status():
    """Показывает статус системы"""
    try:
        from agents_v2 import get_agent_manager
        
        manager = get_agent_manager()
        
        print("\n📊 Статус системы Колыбель v2:")
        print("=" * 50)
        
        # Статус рантаймов
        print("\n🏗️ Рантаймы:")
        runtime_status = manager.get_runtime_status()
        for name, status in runtime_status.items():
            health_icon = "✅" if status.healthy else "❌"
            print(f"   {health_icon} {name.title()}: {'Здоров' if status.healthy else 'Недоступен'}")
        
        # Список агентов
        print("\n🤖 Агенты:")
        agents = manager.list_agents()
        if agents:
            for agent in agents:
                print(f"   • {agent['name']} ({agent['agent_id'][:8]}...)")
                print(f"     Рантайм: {agent['primary_runtime']}")
                print(f"     Выполнений: {agent['execution_count']}")
                print(f"     Успешность: {agent['success_rate']*100:.1f}%")
        else:
            print("   Агенты не найдены")
        
        # Проверка здоровья
        print("\n🔍 Проверка здоровья системы...")
        health_results = manager.orchestrator.force_health_check()
        
        for runtime_name, is_healthy in health_results.items():
            health_icon = "✅" if is_healthy else "❌"
            print(f"   {health_icon} {runtime_name}: {'OK' if is_healthy else 'Недоступен'}")
        
    except Exception as e:
        logger.error(f"Ошибка получения статуса системы: {e}")
        print(f"❌ Ошибка: {e}")

def run_tests():
    """Запускает простые тесты системы"""
    print("\n🧪 Запуск тестов системы...")

    tests_passed = 0
    tests_total = 0

    # Тест 1: Импорт модулей
    tests_total += 1
    try:
        from agents_v2 import AgentManager
        from agent_specification import AgentSpecification
        from runtime_orchestrator import RuntimeOrchestrator
        from runtime_adapters import LocalRuntimeAdapter
        print("✅ Тест 1: Импорт модулей - ПРОЙДЕН")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Тест 1: Импорт модулей - ПРОВАЛЕН ({e})")

    # Тест 2: Создание менеджера агентов
    tests_total += 1
    try:
        from agents_v2 import get_agent_manager
        manager = get_agent_manager()
        print("✅ Тест 2: Создание менеджера агентов - ПРОЙДЕН")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Тест 2: Создание менеджера агентов - ПРОВАЛЕН ({e})")

    # Тест 3: Проверка рантаймов
    tests_total += 1
    try:
        runtime_status = manager.get_runtime_status()
        if runtime_status:
            print("✅ Тест 3: Проверка рантаймов - ПРОЙДЕН")
            tests_passed += 1
        else:
            print("❌ Тест 3: Проверка рантаймов - ПРОВАЛЕН (нет рантаймов)")
    except Exception as e:
        print(f"❌ Тест 3: Проверка рантаймов - ПРОВАЛЕН ({e})")

    # Тест 4: Создание спецификации агента
    tests_total += 1
    try:
        from agent_specification import AgentSpecification, AgentTrigger, AgentStep, TriggerType, StepType
        from datetime import datetime

        spec = AgentSpecification(
            id="test_agent",
            name="Тестовый агент",
            owner="test",
            triggers=[AgentTrigger(type=TriggerType.SCHEDULE, config={"cron": "0 * * * *"})],
            steps=[AgentStep(id="test_step", name="Тест", type=StepType.HTTP_REQUEST, config={})]
        )

        # Валидация спецификации
        errors = spec.validate()
        if not errors:
            print("✅ Тест 4: Создание и валидация спецификации агента - ПРОЙДЕН")
            tests_passed += 1
        else:
            print(f"❌ Тест 4: Создание и валидация спецификации агента - ПРОВАЛЕН ({errors})")
    except Exception as e:
        print(f"❌ Тест 4: Создание спецификации агента - ПРОВАЛЕН ({e})")

    # Тест 5: Проверка работы адаптеров
    tests_total += 1
    try:
        from runtime_adapters import LocalRuntimeAdapter
        adapter = LocalRuntimeAdapter()
        if adapter.is_available():
            print("✅ Тест 5: Проверка локального адаптера - ПРОЙДЕН")
            tests_passed += 1
        else:
            print("❌ Тест 5: Проверка локального адаптера - ПРОВАЛЕН (не доступен)")
    except Exception as e:
        print(f"❌ Тест 5: Проверка локального адаптера - ПРОВАЛЕН ({e})")

    print(f"\n📊 Результаты тестов: {tests_passed}/{tests_total} пройдено")

    if tests_passed == tests_total:
        print("🎉 Все тесты пройдены успешно!")
        return True
    else:
        print("⚠️ Некоторые тесты провалены. Проверьте конфигурацию системы.")
        return False
        print("⚠️ Некоторые тесты провалены. Проверьте конфигурацию системы.")

def main():
    """Главная функция"""
    show_banner()
    
    # Проверяем зависимости
    if not check_dependencies():
        print("❌ Не удалось установить зависимости. Выход.")
        return
    
    # Создаем директории
    create_directories()
    
    while True:
        choice = show_menu()
        
        if choice == '1':
            start_web_interface()
        elif choice == '2':
            run_migration()
        elif choice == '3':
            create_test_agent()
        elif choice == '4':
            show_system_status()
        elif choice == '5':
            run_tests()
        elif choice == '0':
            print("👋 До свидания!")
            break
        else:
            print("❌ Неверный выбор. Попробуйте снова.")
        
        input("\n⏸️ Нажмите Enter для продолжения...")

if __name__ == '__main__':
    main()