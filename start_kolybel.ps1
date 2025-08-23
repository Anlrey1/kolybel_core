#start_kolybel.ps1
Write-Host "🚀 Запуск Колыбели..." -ForegroundColor Cyan

# Переходим в корень проекта
Set-Location "C:\Users\Andrew\kolybel_core"

# Проверка и активация виртуального окружения
$venvPath = ".\venv"
if (-not (Test-Path "$venvPath\Scripts\Activate.ps1")) {
    Write-Host "❌ Виртуальное окружение не найдено!" -ForegroundColor Red
    exit 1
}

if (-not $env:VIRTUAL_ENV) {
    Write-Host "🔧 Активация виртуального окружения..." -ForegroundColor Yellow
    .\venv\Scripts\Activate.ps1
}

# Запуск Ollama и Nginx через docker-compose
docker-compose up -d cradle-llm
Start-Sleep -Seconds 5

# Загрузка моделей Ollama
$models = @("mistral:latest", "nous-hermes:latest", "deepseek-coder:latest", "phi:latest")
foreach ($model in $models) {
    $retry = 0
    do {
        $retry++
        Write-Host "[Попытка $retry] Загрузка модели $model"
        docker exec cradle-llm ollama pull $model
        if ($LASTEXITCODE -eq 0) { break }
        Start-Sleep -Seconds 10
    } while ($retry -lt 3)
}

# Запуск HTTPS-прокси
Set-Location "C:\Users\Andrew\kolybel_core\ollama-https-proxy"
docker rm -f ollama-https-proxy 2>$null
docker-compose up -d ollama-https-proxy
Start-Sleep -Seconds 5

# Проверка работоспособности
$response = curl.exe -k https://localhost/api/tags
if ($response -match "models") {
    Write-Host "✅ Ollama работает через HTTPS-прокси!" -ForegroundColor Green
} else {
    Write-Host "❌ Ошибка подключения к Ollama!" -ForegroundColor Red
    docker logs ollama-https-proxy
    docker logs cradle-llm
}