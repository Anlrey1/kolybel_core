# run_kolybel.ps1

# === Переход в корень проекта ===
$projectRoot = "C:\Users\Andrew\kolybel_core"
Set-Location $projectRoot

# === Проверка venv ===
$venvPath = ".\venv"
if (-not (Test-Path "$venvPath\Scripts\Activate.ps1")) {
    Write-Host "❌ Виртуальное окружение не найдено!" -ForegroundColor Red
    exit 1
}

# === Активация venv ===
if (-not $env:VIRTUAL_ENV) {
    Write-Host "🔧 Активация виртуального окружения..." -ForegroundColor Yellow
    try {
        .\venv\Scripts\Activate.ps1
    } catch {
        Write-Host "❌ Ошибка активации venv: $_" -ForegroundColor Red
        exit 1
    }
}

Write-Host "🚀 Запуск Колыбели..." -ForegroundColor Cyan

# === Форматирование кода (не обязательное) ===
Write-Host "📐 Автоформатирование через Black..."
try {
    black main.py core.py llm.py memory_core.py --line-length 88
} catch {
    Write-Host "⚠️ Black не установлен. Можно установить: pip install black" -ForegroundColor Yellow
}

# === Проверка синтаксиса ===
Write-Host "🧼 Проверка синтаксиса через py_compile..." -ForegroundColor White
$syntaxOk = $true
$files = @("main.py", "core.py", "llm.py", "memory_core.py", "agents.py", "template_engine.py", "prompt_templates_loader.py")

foreach ($file in $files) {
    python -m py_compile $file
    if ($LastExitCode -ne 0) {
        Write-Host "❌ Ошибка в файле: $file" -ForegroundColor Red
        $syntaxOk = $false
    }
}

if (-not $syntaxOk) {
    Write-Host "⛔ Запуск остановлен из-за ошибок синтаксиса!" -ForegroundColor Red
    exit 1
}

# === Запуск Docker-сервисов ===
Write-Host "🐳 Подготовка: загрузка моделей..."
docker-compose down
docker-compose up -d --remove-orphans

# === Ожидание Ollama ===
Write-Host "⏳ Ожидание инициализации Ollama..."
do {
    try {
        $status = docker inspect cradle-llm --format "{{.State.Health.Status}}"
    } catch {
        Write-Host "🔄 Ожидаем Docker API..."
        Start-Sleep -Seconds 5
        continue
    }

    Write-Host "Статус: $status"
    Start-Sleep -Seconds 5
} while ($status -ne "healthy")

# === Проверка HTTPS-прокси ===
Write-Host "🔗 Проверка HTTPS-прокси..." -ForegroundColor Green
$response = curl.exe -k https://localhost/api/tags 

if ($response.StatusCode -eq 200) {
    Write-Host "✅ Ollama работает через HTTPS!"
} else {
    Write-Host "❌ Прокси возвращает код: $($response.StatusCode)" -ForegroundColor Red
    docker logs ollama-https-proxy
    exit 1
}

# === Запуск основной программы ===
Write-Host "🧠 Запуск Колыбели..." -ForegroundColor Cyan
python main.py

Write-Host "👋 Работа Колыбели завершена." -ForegroundColor Yellow