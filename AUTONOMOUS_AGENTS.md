# 🤖 Автономная система агентов Колыбели

## Обзор

Колыбель теперь может работать **полностью автономно** без зависимости от n8n или других внешних сервисов. Система автоматически переключается на автономных агентов, если n8n недоступен.

## 🎯 Ключевые возможности

### ✅ Полная автономность

- Работа без n8n, Make.com или других внешних платформ
- Локальное выполнение всех задач
- Встроенный планировщик задач
- Персистентное хранение состояния

### 🔄 Гибридный режим

- Автоматический fallback: n8n → автономные агенты
- Сохранение всех возможностей при отказе внешних сервисов
- Единый API для управления всеми типами агентов

### 📊 Мониторинг и аналитика

- Детальное логирование выполнения
- Статистика успешности
- Система уведомлений об ошибках

## 🛠️ Типы автономных агентов

### 1. RSS Monitor Agent

```python
# Мониторинг RSS лент и автоматическая публикация
create_agent_from_plan(
    memory=memory,
    rss_url="https://example.com/rss",
    chat_id="@your_channel",
    style="информативный стиль",
    use_n8n=False  # Принудительно автономный
)
```

**Возможности:**

- Парсинг RSS/Atom лент
- Обработка контента через LLM
- Автоматическая публикация в Telegram
- Дедупликация (не публикует повторы)
- Настраиваемое расписание

### 2. Content Generator Agent

```python
# Генерация контента по шаблонам
create_content_agent(
    memory=memory,
    template_id="technology_template",
    chat_id="@tech_channel",
    topics=["ИИ", "блокчейн", "квантовые компьютеры"],
    schedule="every 4 hours"
)
```

**Возможности:**

- Использование системы шаблонов Колыбели
- Генерация по заданным темам или трендам
- Адаптивный контент на основе памяти
- Автоматическое добавление хэштегов

### 3. Channel Manager Agent

```python
# Управление каналом и аудиторией
create_channel_manager_agent(
    memory=memory,
    chat_id="@managed_channel",
    actions=["analytics", "engagement", "moderation"]
)
```

**Возможности:**

- Анализ активности канала
- Повышение вовлеченности аудитории
- Модерация контента
- Планирование активностей

## 🚀 Быстрый старт

### 1. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 2. Настройка переменных окружения

```bash
# Обязательные
export TELEGRAM_TOKEN="your_bot_token"

# Опциональные (для n8n)
export N8N_API_URL="http://localhost:5678/api/workflows"
export N8N_USER="admin"
export N8N_PASSWORD="password"
```

### 3. Запуск системы

```bash
python main.py
```

### 4. Создание агентов

```bash
# В интерфейсе Колыбели
agents                    # Показать статус
start-agents             # Запустить планировщик
stop-agents              # Остановить планировщик

# Или через демо-скрипт
python demo_autonomous_agents.py
```

## 📋 Команды управления

### В основном интерфейсе (main.py):

- `agents` - статус всех агентов
- `start-agents` - запуск автономной системы
- `stop-agents` - остановка системы
- `audit` - аудит агентов (включая автономных)
- `stats` - статистика производительности

### Программный API:

```python
from agents import (
    get_agents_status,
    start_autonomous_system,
    stop_autonomous_system
)

# Статус системы
status = get_agents_status(memory)

# Управление
start_autonomous_system(memory)
stop_autonomous_system(memory)
```

## 🔧 Конфигурация агентов

### Структура задачи агента:

```python
{
    "name": "Мой RSS агент",
    "description": "Мониторинг технических новостей",
    "type": "rss_monitor",  # rss_monitor, content_generator, channel_manager
    "schedule": "0 9,15,20 * * *",  # Cron или "every X hours"
    "config": {
        "rss_url": "https://example.com/rss",
        "chat_id": "@channel",
        "style": "профессиональный стиль",
        "max_posts": 3
    }
}
```

### Расписание:

- **Cron формат**: `"0 9,15,20 * * *"` (в 9:00, 15:00, 20:00)
- **Простой формат**: `"every 3 hours"`, `"every 30 minutes"`

## 📁 Структура файлов

```
kolybel_core/
├── autonomous_agents.py      # Основной модуль автономных агентов
├── agents.py                 # Гибридная система (n8n + автономные)
├── telegram_bridge.py        # Упрощенный Telegram API
├── autonomous_agents/        # Сохраненные задачи агентов
│   ├── agent_20241201_120000.json
│   └── agent_20241201_130000.json
├── agent_logs/              # Логи выполнения
│   ├── agent_20241201_120000_202412.log
│   └── usage.log
└── demo_autonomous_agents.py # Демонстрация
```

## 🔍 Мониторинг и отладка

### Логи агентов:

```bash
# Общий лог использования
tail -f agent_logs/usage.log

# Детальные логи конкретного агента
tail -f agent_logs/agent_ID_YYYYMM.log
```

### Статус в реальном времени:

```python
# В Python коде
from autonomous_agents import get_agent_manager

manager = get_agent_manager(memory)
agents = manager.list_agents()

for agent in agents:
    print(f"{agent['name']}: {agent['success_rate']:.1f}% успешность")
```

## 🛡️ Отказоустойчивость

### Автоматический fallback:

1. **Попытка n8n** (если настроен)
2. **Переключение на автономного агента** (при ошибке)
3. **Сохранение всех возможностей**

### Восстановление после сбоев:

- Автоматическая загрузка задач при перезапуске
- Сохранение состояния в файлах
- Логирование всех ошибок
- Продолжение работы других агентов при сбое одного

## 🎛️ Расширение системы

### Создание нового типа агента:

```python
from autonomous_agents import BaseAgent

class MyCustomAgent(BaseAgent):
    def execute(self) -> bool:
        try:
            # Ваша логика здесь
            self.log_execution(True, "Успешно выполнено")
            return True
        except Exception as e:
            self.log_execution(False, f"Ошибка: {e}")
            return False
```

### Интеграция в систему:

```python
# В autonomous_agents.py добавить в create_agent()
elif task.task_type == "my_custom":
    agent = MyCustomAgent(task, self.memory)
```

## 🔮 Будущие возможности

- **Веб-интерфейс** для управления агентами
- **API endpoints** для внешних интеграций
- **Машинное обучение** для оптимизации расписания
- **Распределенная система** для масштабирования
- **Интеграция с другими платформами** (Discord, VK, etc.)

## ❓ FAQ

**Q: Что происходит, если n8n перестанет работать?**
A: Система автоматически переключится на автономных агентов без потери функциональности.

**Q: Можно ли использовать только автономных агентов?**
A: Да, установите `use_n8n=False` при создании агентов или не настраивайте N8N переменные.

**Q: Как добавить новый источник RSS?**
A: Создайте нового агента с другим `rss_url` или добавьте URL в конфигурацию существующего.

**Q: Безопасно ли оставлять систему работать 24/7?**
A: Да, система спроектирована для непрерывной работы с обработкой ошибок и логированием.

---

**🎉 Колыбель теперь полностью автономна и готова работать независимо от внешних сервисов!**
