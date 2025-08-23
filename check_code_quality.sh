#check_code_quality.sh

# Переход в виртуальное окружение (если не активно)
if [ -z "$VIRTUAL_ENV" ]; then
    echo "🔧 Активация виртуального окружения..."
    source venv/bin/activate || { echo "❌ Ошибка активации venv"; exit 1; }
fi

# 1. Статический анализ
echo "🔍 Запуск flake8..."
flake8 . --exclude=venv,__pycache__ --max-line-length=120 || exit 1

echo "🔍 Запуск mypy..."
mypy . --ignore-missing-imports || exit 1

echo "🔍 Запуск bandit..."
bandit -r . -x venv,__pycache__ || exit 1

echo "🔍 Запуск pylint..."
pylint **/*.py --ignore=venv || exit 1

# 2. Проверка зависимостей
echo "📦 Проверка уязвимостей в зависимостях..."
safety check --full-report || exit 1

# 3. Поиск случайных print() и лишних логов
echo "📜 Поиск print() и logging.info()..."
grep -rn "print(" . --include="*.py" --exclude-dir={venv,__pycache__} && \
  { echo "❌ Найдены print() - замените на logging"; exit 1; }

grep -rn "logging\.info" . --include="*.py" --exclude-dir={venv,__pycache__} && \
  { echo "❌ Найдены logging.info() - в продакшене используйте logging.warning"; exit 1; }

# 4. Проверка Docker (требует установки Docker)
echo "🐳 Сканирование образов на уязвимости..."
docker scan ollama-https-proxy || exit 1
docker scan cradle-llm || exit 1

echo "✅ Все проверки пройдены успешно!"