# main_v2.py — обновленная точка входа с новой архитектурой
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
from agents_v2 import get_agent_manager, AgentManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

memory = MemoryCore()

def load_manifest_to_memory(mem: MemoryCore):
    """Загружает манифест в память"""
    try:
        if os.path.isfile("kolybel_manifest.txt"):
            with open("kolybel_manifest.txt", "r", encoding="utf-8") as f:
                txt = f.read()
                mem.store(f"[manifest] {txt}", {
                          "type": "system", "source": "manual"})
                print("📜 Манифест загружен в память.")
    except Exception as e:
        print(f"⚠️ Ошибка загрузки манифеста: {e}")

def initialize_system():
    """Инициализирует систему Колыбели v2"""
    print("🌟 Инициализация Колыбели v2 с независимой архитектурой")
    print("=" * 60)
    
    # Загружаем манифест
    load_manifest_to_memory(memory)
    
    # Инициализируем менеджер агентов
    try:
        agent_manager = get_agent_manager(memory, {
            'execution_policy': 'failover',
            'health_check_interval': 60,
            'docker_enabled': True,
            'max_concurrent_local': 5
        })
        print("🤖 Менеджер агентов v2 инициализирован")
        print(f"🏗️ Доступные рантаймы: {list(agent_manager.orchestrator.adapters.keys())}")
        
        # Показываем статус рантаймов
        health = agent_manager.get_runtime_health()
        for runtime, status in health.items():
            status_icon = "✅" if status['is_healthy'] else "❌"
            print(f"   {status_icon} {runtime}: {'Здоров' if status['is_healthy'] else 'Нездоров'}")
        
    except Exception as e:
        print(f"⚠️ Ошибка инициализации менеджера агентов: {e}")
        return None
    
    print("=" * 60)
    return agent_manager

def show_main_menu():
    """Показывает главное меню"""
    print("\n🎯 Колыбель v2 - Главное меню")
    print("=" * 40)
    print("1. 💬 Диалог с Колыбелью")
    print("2. 🤖 Управление агентами")
    print("3. 🎯 Управление целями")
    print("4. 📊 Статистика системы")
    print("5. 🌐 Запустить веб-интерфейс")
    print("6. 📤 Экспорт/Импорт агентов")
    print("7. ⚙️ Настройки")
    print("0. 🚪 Выход")
    print("=" * 40)

def handle_dialog_mode(agent_manager: AgentManager):
    """Режим диалога с Колыбелью"""
    print("\n💬 Режим диалога активирован")
    print("Введите 'exit' для выхода в главное меню")
    print("-" * 40)
    
    while True:
        try:
            user_input = input("\n🔹 Вы: ").strip()
            
            if user_input.lower() in ['exit', 'выход', 'quit']:
                break
            
            if not user_input:
                continue
            
            # Обрабатываем системные команды
            if user_input.startswith(("goal:", "mission", "remind", "audit", "stats", "agents")):
                if user_input.startswith("agents"):
                    handle_agents_command(user_input, agent_manager)
                else:
                    response = handle_system_commands(user_input)
                    print(f"🤖 Колыбель: {response}")
            else:
                # Обычный диалог
                response = handle_user_input(user_input)
                print(f"🤖 Колыбель: {response}")
                
        except KeyboardInterrupt:
            print("\n\n👋 Возврат в главное меню...")
            break
        except Exception as e:
            print(f"❌ Ошибка: {e}")

def handle_agents_command(command: str, agent_manager: AgentManager):
    """Обрабатывает команды управления агентами"""
    parts = command.split()
    
    if len(parts) == 1:  # Просто "agents"
        show_agents_status(agent_manager)
    elif parts[1] == "create":
        create_agent_interactive(agent_manager)
    elif parts[1] == "list":
        show_agents_status(agent_manager)
    elif parts[1] == "delete" and len(parts) > 2:
        delete_agent_interactive(agent_manager, parts[2])
    else:
        print("Доступные команды:")
        print("  agents - показать статус агентов")
        print("  agents create - создать нового агента")
        print("  agents list - список агентов")
        print("  agents delete <id> - удалить агента")

def show_agents_status(agent_manager: AgentManager):
    """Показывает статус всех агентов"""
    try:
        status = agent_manager.get_all_agents_status()
        
        print(f"\n🤖 Статус агентов (всего: {status['total_agents']})")
        print("-" * 50)
        
        if status['total_agents'] == 0:
            print("Нет развернутых агентов")
            return
        
        for agent_id, agent_data in status['agents'].items():
            success_rate = agent_data.get('success_rate', 0) * 100
            print(f"📋 {agent_data.get('name', 'Unknown')} ({agent_id[:8]}...)")
            print(f"   Основной рантайм: {agent_data.get('primary_runtime', 'unknown')}")
            print(f"   Успешность: {success_rate:.1f}%")
            print(f"   Выполнений: {agent_data.get('execution_count', 0)}")
            print(f"   Последнее выполнение: {agent_data.get('last_execution', 'Никогда')}")
            print()
        
        # Показываем здоровье рантаймов
        print("🏥 Здоровье рантаймов:")
        health = status.get('runtime_health', {})
        for runtime, health_data in health.items():
            status_icon = "✅" if health_data.get('is_healthy', False) else "❌"
            print(f"   {status_icon} {runtime}")
        
    except Exception as e:
        print(f"❌ Ошибка получения статуса агентов: {e}")

def create_agent_interactive(agent_manager: AgentManager):
    """Интерактивное создание агента"""
    print("\n🛠️ Создание нового агента")
    print("-" * 30)
    
    try:
        # Выбор типа агента
        print("Выберите тип агента:")
        print("1. RSS Монитор")
        print("2. Генератор контента")
        print("3. Пользовательский агент")
        
        choice = input("Ваш выбор (1-3): ").strip()
        
        if choice == "1":
            create_rss_agent_interactive(agent_manager)
        elif choice == "2":
            create_content_agent_interactive(agent_manager)
        elif choice == "3":
            create_custom_agent_interactive(agent_manager)
        else:
            print("❌ Неверный выбор")
    
    except Exception as e:
        print(f"❌ Ошибка создания агента: {e}")

def create_rss_agent_interactive(agent_manager: AgentManager):
    """Создание RSS агента"""
    name = input("Название агента: ").strip()
    rss_url = input("RSS URL: ").strip()
    chat_id = input("Telegram канал/чат ID: ").strip()
    style = input("Стиль обработки (по умолчанию 'информативный'): ").strip() or "информативный стиль"
    
    # Выбор рантаймов
    print("\nВыберите предпочитаемые рантаймы (через запятую):")
    print("Доступные: local, n8n, docker")
    runtimes_input = input("Рантаймы (по умолчанию 'local,n8n'): ").strip()
    
    if runtimes_input:
        runtime_preferences = [r.strip() for r in runtimes_input.split(',')]
    else:
        runtime_preferences = ['local', 'n8n']
    
    try:
        agent_id = agent_manager.create_rss_agent(
            name=name,
            owner="console_user",
            rss_url=rss_url,
            telegram_chat_id=chat_id,
            style=style,
            runtime_preferences=runtime_preferences
        )
        
        print(f"✅ RSS агент '{name}' создан с ID: {agent_id}")
        
    except Exception as e:
        print(f"❌ Ошибка создания RSS агента: {e}")

def create_content_agent_interactive(agent_manager: AgentManager):
    """Создание агента генерации контента"""
    name = input("Название агента: ").strip()
    template_id = input("ID шаблона: ").strip()
    chat_id = input("Telegram канал/чат ID: ").strip()
    topics_input = input("Темы (через запятую): ").strip()
    topics = [t.strip() for t in topics_input.split(',') if t.strip()]
    
    try:
        agent_id = agent_manager.create_content_agent(
            name=name,
            owner="console_user",
            template_id=template_id,
            telegram_chat_id=chat_id,
            topics=topics
        )
        
        print(f"✅ Контент агент '{name}' создан с ID: {agent_id}")
        
    except Exception as e:
        print(f"❌ Ошибка создания контент агента: {e}")

def create_custom_agent_interactive(agent_manager: AgentManager):
    """Создание пользовательского агента"""
    print("Для создания пользовательского агента используйте:")
    print("1. Веб-интерфейс (более удобно)")
    print("2. Импорт из JSON/YAML файла")
    
    choice = input("Ваш выбор (1-2): ").strip()
    
    if choice == "2":
        file_path = input("Путь к файлу спецификации: ").strip()
        try:
            agent_id = agent_manager.import_agent_from_file(file_path)
            print(f"✅ Агент импортирован с ID: {agent_id}")
        except Exception as e:
            print(f"❌ Ошибка импорта агента: {e}")
    else:
        print("💡 Запустите веб-интерфейс командой '5' в главном меню")

def delete_agent_interactive(agent_manager: AgentManager, agent_id: str):
    """Удаление агента"""
    try:
        # Получаем информацию об агенте
        status = agent_manager.get_agent_status(agent_id)
        if status.get('status') == 'not_deployed':
            print(f"❌ Агент {agent_id} не найден")
            return
        
        agent_name = status.get('name', 'Unknown')
        confirm = input(f"Удалить агента '{agent_name}' ({agent_id})? (y/N): ").strip().lower()
        
        if confirm == 'y':
            success = agent_manager.delete_agent(agent_id)
            if success:
                print(f"✅ Агент '{agent_name}' удален")
            else:
                print(f"❌ Не удалось удалить агента")
        else:
            print("Отменено")
            
    except Exception as e:
        print(f"❌ Ошибка удаления агента: {e}")

def handle_agents_menu(agent_manager: AgentManager):
    """Меню управления агентами"""
    while True:
        print("\n🤖 Управление агентами")
        print("-" * 30)
        print("1. Показать статус агентов")
        print("2. Создать нового агента")
        print("3. Удалить агента")
        print("4. Выполнить агента вручную")
        print("5. Экспорт агента")
        print("0. Назад в главное меню")
        
        choice = input("\nВаш выбор: ").strip()
        
        if choice == "0":
            break
        elif choice == "1":
            show_agents_status(agent_manager)
        elif choice == "2":
            create_agent_interactive(agent_manager)
        elif choice == "3":
            agent_id = input("ID агента для удаления: ").strip()
            delete_agent_interactive(agent_manager, agent_id)
        elif choice == "4":
            execute_agent_interactive(agent_manager)
        elif choice == "5":
            export_agent_interactive(agent_manager)
        else:
            print("❌ Неверный выбор")

def execute_agent_interactive(agent_manager: AgentManager):
    """Выполнение агента вручную"""
    agent_id = input("ID агента для выполнения: ").strip()
    
    try:
        print(f"🚀 Выполнение агента {agent_id}...")
        result = agent_manager.execute_agent(agent_id)
        
        if result.success:
            print(f"✅ Агент выполнен успешно за {result.execution_time:.2f}с")
            if result.logs:
                print("📋 Логи выполнения:")
                for log in result.logs:
                    print(f"   {log}")
        else:
            print(f"❌ Ошибка выполнения: {result.error}")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")

def export_agent_interactive(agent_manager: AgentManager):
    """Экспорт агента"""
    agent_id = input("ID агента для экспорта: ").strip()
    format_choice = input("Формат (json/yaml, по умолчанию json): ").strip().lower() or "json"
    file_path = input(f"Путь для сохранения (по умолчанию agent_{agent_id}.{format_choice}): ").strip()
    
    if not file_path:
        file_path = f"agent_{agent_id}.{format_choice}"
    
    try:
        agent_manager.export_agent_to_file(agent_id, file_path, format_choice)
        print(f"✅ Агент экспортирован в {file_path}")
    except Exception as e:
        print(f"❌ Ошибка экспорта: {e}")

def launch_web_interface():
    """Запуск веб-интерфейса"""
    print("\n🌐 Запуск веб-интерфейса...")
    try:
        import subprocess
        subprocess.run(["python", "start_web_interface.py"])
    except Exception as e:
        print(f"❌ Ошибка запуска веб-интерфейса: {e}")
        print("💡 Попробуйте запустить вручную: python start_web_interface.py")

def main():
    """Основная функция"""
    # Простая авторизация
    SECRET_KEY = "привет"
    while True:
        code = input("🔹 Введите код авторизации: ").strip()
        if code == SECRET_KEY:
            print("🔐 Авторизация успешна. Добро пожаловать в Колыбель v2!")
            break
        print("❌ Неверный код. Попробуйте снова.")
    
    # Инициализация системы
    agent_manager = initialize_system()
    if not agent_manager:
        print("❌ Не удалось инициализировать систему")
        return
    
    # Главный цикл
    while True:
        try:
            show_main_menu()
            choice = input("\nВаш выбор: ").strip()
            
            if choice == "0":
                print("\n👋 До свидания!")
                agent_manager.stop()
                break
            elif choice == "1":
                handle_dialog_mode(agent_manager)
            elif choice == "2":
                handle_agents_menu(agent_manager)
            elif choice == "3":
                print("🎯 Управление целями (используйте команды goal: в диалоге)")
            elif choice == "4":
                show_agents_status(agent_manager)
            elif choice == "5":
                launch_web_interface()
            elif choice == "6":
                print("📤 Экспорт/Импорт доступен в меню агентов")
            elif choice == "7":
                print("⚙️ Настройки доступны в веб-интерфейсе")
            else:
                print("❌ Неверный выбор")
                
        except KeyboardInterrupt:
            print("\n\n👋 Выход из программы...")
            agent_manager.stop()
            break
        except Exception as e:
            print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    main()