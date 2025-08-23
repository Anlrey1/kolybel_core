#stop_kolybel.ps1
Write-Host "🛑 Остановка Колыбели..." -ForegroundColor Yellow

# Останавливаем прокси
docker stop ollama-https-proxy
docker rm ollama-https-proxy

# Останавливаем Ollama (но сохраняем том с моделями)
Set-Location "C:\Users\Andrew\kolybel_core"
docker-compose down

Write-Host "✅ Колыбель остановлена. Модели сохранены." -ForegroundColor Green