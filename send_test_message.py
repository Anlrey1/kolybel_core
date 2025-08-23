# send_test_message.py — публикация от имени бота в канал

import requests
from config import TELEGRAM_TOKEN  # токен уже берётся из .env

# Имя твоего канала
channel_username = "@firepulse18"
text = "🔥 Привет! Это тест от Колыбели."

# URL для API Telegram
url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

# Отправка POST-запроса
response = requests.post(url, data={"chat_id": channel_username, "text": text})

# Печать результата
print("Status:", response.status_code)
print("Ответ:", response.text)
