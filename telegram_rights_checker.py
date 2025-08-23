# telegram_rights_checker.py
import requests
import os
import sys
from config import TELEGRAM_TOKEN


def check_bot_admin_rights(channel_username):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getChatMember"
    params = {"chat_id": channel_username, "user_id": get_bot_user_id()}
    response = requests.get(url, params=params)
    data = response.json()

    if not data.get("ok"):
        print("❌ Ошибка проверки прав:", data.get("description"))
        return

    status = data["result"]["status"]
    print(f"Бот имеет статус в {channel_username}: {status}")
    if status == "administrator":
        print("✅ Бот является администратором канала.")
    else:
        print(
            "⚠️ Бот НЕ является администратором. Нужно добавить его вручную через Telegram."
        )


def get_bot_user_id():
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getMe"
    response = requests.get(url)
    data = response.json()

    if not data.get("ok"):
        raise Exception("Не удалось получить информацию о боте")

    return data["result"]["id"]


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("⚠️ Укажи username канала при запуске скрипта!")
        print("Пример: python telegram_rights_checker.py @firepulse18")
    else:
        channel_username = sys.argv[1]
        check_bot_admin_rights(channel_username)
