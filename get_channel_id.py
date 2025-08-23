# get_channel_id.py
import requests

TOKEN = "7950098219:AAERD98L2hQb8mAeX8laxIg3zYj2Aojv4HQ"
CHANNEL = "@firepulse18"  # Юзернейм канала, если нет ID

message = "🔔 Тестовое сообщение от Колыбели"

# Отправка сообщения
send_url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
send_response = requests.post(send_url, data={"chat_id": CHANNEL, "text": message})
print("Ответ на отправку:", send_response.json())

# Получение ID
updates_url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
updates_response = requests.get(updates_url)
print("Ответ от getUpdates:", updates_response.json())
