#!/usr/bin/env python3
# demo_autonomous_agents.py — демонстрация создания автономных агентов

from memory_core import MemoryCore
from agents import (
    create_agent_from_plan,
    create_content_agent,
    create_channel_manager_agent,
    get_agents_status
)


def demo_create_agents():
    """Демонстрация создания различных типов агентов"""

    print("🚀 Демонстрация создания автономных агентов")
    print("=" * 50)

    memory = MemoryCore()

    # 1. RSS мониторинг агент
    print("\n1️⃣ Создание RSS мониторинг агента...")
    rss_agent_id = create_agent_from_plan(
        memory=memory,
        rss_url="https://dtf.ru/rss",
        chat_id="-1002669388680",
        style="в стиле для подростков до 18 лет",
        use_n8n=False  # Принудительно используем автономного агента
    )
    print(f"✅ RSS агент создан: {rss_agent_id}")

    # 2. Агент генерации контента
    print("\n2️⃣ Создание агента генерации контента...")
    content_agent_id = create_content_agent(
        memory=memory,
        template_id="technology_template",
        chat_id="-1002669388680",
        topics=["искусственный интеллект", "блокчейн", "квантовые компьютеры"],
        schedule="every 6 hours"
    )
    print(f"✅ Агент контента создан: {content_agent_id}")

    # 3. Агент управления каналом
    print("\n3️⃣ Создание агента управления каналом...")
    manager_agent_id = create_channel_manager_agent(
        memory=memory,
        chat_id="-1002669388680",
        actions=["analytics", "engagement", "moderation"]
    )
    print(f"✅ Агент управления создан: {manager_agent_id}")

    # 4. Показываем статус всех агентов
    print("\n📊 Статус всех агентов:")
    print("-" * 30)
    status = get_agents_status(memory)

    print(f"Всего агентов: {status['total_agents']}")
    print(f"Автономных: {status['autonomous_count']}")
    print(f"N8N: {status['n8n_count']}")
    print(
        f"Планировщик: {'🟢 РАБОТАЕТ' if status['scheduler_running'] else '🔴 ОСТАНОВЛЕН'}")

    if status['autonomous_agents']:
        print("\n🤖 Автономные агенты:")
        for agent in status['autonomous_agents']:
            status_icon = "🟢" if agent.get('is_active') else "🔴"
            print(f"  {status_icon} {agent['name']} ({agent['type']})")
            print(f"     Успешность: {agent.get('success_rate', 0):.1f}%")
            print(f"     Последний запуск: {agent.get('last_run', 'Никогда')}")

    print("\n✨ Демонстрация завершена!")
    print("💡 Агенты будут работать автономно по расписанию")
    print("🔧 Используйте команду 'agents' в main.py для мониторинга")


if __name__ == "__main__":
    demo_create_agents()
