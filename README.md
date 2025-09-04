# 🤖 Колыбель v2 - Автономный Интеллектуальный Ассистент

> **Независимая архитектура агентов с автоматическим failover**

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://python.org)
[![Architecture](https://img.shields.io/badge/Architecture-Independent-green.svg)](ARCHITECTURE_V2.md)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 🎯 Что такое Колыбель v2?

Колыбель v2 - это революционная система автономных интеллектуальных агентов с **независимой архитектурой**, которая обеспечивает:

- 🏗️ **Независимость от рантайма** - агенты работают в любой среде
- 🔄 **Автоматический failover** - переключение при сбоях
- 📈 **Масштабируемость** - от локального выполнения до Kubernetes
- 🛡️ **Надежность** - система продолжает работать при любых сбоях
- 🎨 **Современный интерфейс** - веб-панель управления

## ✨ Ключевые особенности

### 🏛️ Независимая архитектура

- **Нейтральный формат** спецификаций агентов (JSON/YAML)
- **Множественные рантаймы** - Local, N8N, Docker, Kubernetes
- **Автоматический failover** между рантаймами
- **Единый API** для управления агентами

### 🤖 Типы агентов

- **RSS Мониторы** - отслеживание новостных лент
- **Контент-генераторы** - создание уникального контента
- **Планировщики задач** - выполнение по расписанию
- **Веб-скраперы** - сбор данных с сайтов
- **Telegram боты** - интеграция с мессенджерами

### 🌐 Веб-интерфейс

- **Дашборд** с общей статистикой
- **Управление агентами** - создание, редактирование, удаление
- **Мониторинг рантаймов** - статус и здоровье системы
- **Инструменты миграции** - перенос существующих агентов
- **REST API** для интеграции

## 🚀 Быстрый старт

### 1. Установка зависимостей

```bash
# Клонируйте репозиторий
git clone <repository-url>
cd kolybel_v2

# Установите зависимости
pip install -r requirements.txt
```

### 2. Запуск системы

```bash
# Интерактивный запуск
python start_kolybel.py
```

Или запустите веб-интерфейс напрямую:

```bash
# Запуск веб-интерфейса
python web_interface.py
```

### 3. Доступ к веб-интерфейсу

Откройте браузер и перейдите по адресу: **http://127.0.0.1:5000**

## 📋 Доступные страницы

- **Дашборд**: `/` - общая статистика и обзор системы
- **Агенты**: `/agents` - список всех агентов
- **Создать агента**: `/agents/create` - форма создания нового агента
- **Рантаймы**: `/runtimes` - статус всех рантаймов
- **Миграция**: `/migration` - инструменты миграции агентов

## 🔧 API Endpoints

### Агенты
- `GET /api/agents` - список агентов
- `POST /agents/<id>/execute` - выполнить агента
- `POST /agents/<id>/delete` - удалить агента

### Система
- `GET /api/runtimes` - статус рантаймов
- `GET /api/health` - проверка здоровья системы

## 💻 Программное использование

### Создание RSS агента

```python
from agents_v2 import get_agent_manager

manager = get_agent_manager()

agent_id = manager.create_rss_agent(
    name="DTF Monitor",
    owner="user",
    rss_url="https://dtf.ru/rss",
    telegram_chat_id="-1002669388680",
    schedule="0 9,15,20 * * *",  # 3 раза в день
    style="краткий информативный стиль"
)

print(f"Агент создан с ID: {agent_id}")
```

### Создание контент-генератора

```python
agent_id = manager.create_content_agent(
    name="Генератор постов",
    owner="user",
    template_id="social_post",
    telegram_chat_id="-1002669388680",
    topics=["технологии", "игры", "новости"],
    schedule="0 12 * * *"  # Каждый день в полдень
)
```

### Выполнение агента

```python
result = manager.execute_agent(agent_id)
print(f"Статус: {result.status}")
print(f"Время выполнения: {result.execution_time}с")
```

## 🔄 Миграция существующих агентов

### Автоматическая миграция

```python
from migration_tool import AgentMigrationTool

migration = AgentMigrationTool()

# Мигрировать n8n workflows из approved_goals
migrated_agents = migration.migrate_n8n_workflows_from_approved_goals()

# Сгенерировать отчет
migration.save_migration_report("migration_report.json")
```

### Через веб-интерфейс

1. Перейдите на страницу **Миграция** (`/migration`)
2. Нажмите **"Запустить миграцию"**
3. Просмотрите отчет о миграции

## 🏗️ Архитектура системы

```
kolybel_v2/
├── agent_specification.py      # Нейтральный формат спецификаций
├── runtime_adapters.py         # Адаптеры рантаймов
├── runtime_orchestrator.py     # Оркестратор выполнения
├── agents_v2.py               # Менеджер агентов
├── web_interface.py           # Веб-интерфейс
├── migration_tool.py          # Инструмент миграции
├── start_kolybel.py          # Главный скрипт запуска
├── autonomous_agents.py       # Мост совместимости
└── intuition.py              # Система интуиции
```

## 🔧 Конфигурация

### Переменные окружения

```bash
# Веб-интерфейс
HOST=127.0.0.1          # Хост веб-сервера
PORT=5000               # Порт веб-сервера
DEBUG=False             # Режим отладки
SECRET_KEY=your_secret  # Секретный ключ Flask

# Telegram
TELEGRAM_BOT_TOKEN=your_token
TELEGRAM_CHAT_ID=your_chat_id

# N8N
N8N_API_URL=http://localhost:5678
N8N_API_KEY=your_api_key

# Docker
DOCKER_HOST=unix:///var/run/docker.sock
```

### Настройка рантаймов

Система автоматически определяет доступные рантаймы:

- **Local** - всегда доступен
- **N8N** - если доступен API N8N
- **Docker** - если доступен Docker daemon
- **Kubernetes** - если настроен kubectl

## 🧪 Тестирование

```bash
# Запуск тестов через интерфейс
python start_kolybel.py
# Выберите пункт "5. Запустить тесты"

# Создание тестового агента
python start_kolybel.py
# Выберите пункт "3. Создать тестового агента"
```

## 📊 Мониторинг

### Веб-дашборд

- Общая статистика агентов
- Статус рантаймов в реальном времени
- История выполнений
- Метрики успешности

### Логи

```bash
# Логи агентов
tail -f agent_logs/*.log

# Логи системы
tail -f awakening.log
```

## 🔍 Устранение неполадок

### Агент не выполняется

1. Проверьте статус рантаймов на странице `/runtimes`
2. Убедитесь, что все зависимости установлены
3. Проверьте логи агента в `agent_logs/`

### Веб-интерфейс не запускается

1. Убедитесь, что Flask установлен: `pip install flask`
2. Проверьте, что порт 5000 свободен
3. Запустите с отладкой: `DEBUG=True python web_interface.py`

### Проблемы с рантаймами

1. **Local**: всегда должен работать
2. **N8N**: проверьте доступность API
3. **Docker**: убедитесь, что Docker запущен
4. **Kubernetes**: проверьте конфигурацию kubectl

## 🤝 Обратная совместимость

Система поддерживает старые API для плавной миграции:

```python
# Старый API (устарел, но работает)
from autonomous_agents import create_autonomous_agent_from_plan

# Новый API (рекомендуется)
from agents_v2 import get_agent_manager
```

## 📈 Планы развития

- [ ] Kubernetes оператор
- [ ] Расширенная система мониторинга
- [ ] Интеграция с Prometheus/Grafana
- [ ] Веб-редактор спецификаций агентов
- [ ] Marketplace агентов
- [ ] Система плагинов

## 📄 Лицензия

MIT License - см. файл [LICENSE](LICENSE)

## 🆘 Поддержка

Если у вас возникли вопросы или проблемы:

1. Проверьте [документацию](ARCHITECTURE_V2.md)
2. Запустите диагностику: `python start_kolybel.py` → "4. Показать статус системы"
3. Создайте issue в репозитории

---

**Колыбель v2** - ваш надежный помощник в мире автономных агентов! 🚀