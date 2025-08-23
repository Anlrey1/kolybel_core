#pull_ollama_models.ps1
Write-Host "Подключение к контейнеру cradle-llm..."
docker exec cradle-llm ollama pull nous-hermes
docker exec cradle-llm ollama pull mistral
docker exec cradle-llm ollama pull phi
docker exec cradle-llm ollama pull deepseek-coder
Write-Host "Все модели успешно загружены."
