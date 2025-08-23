import requests
import json
import logging

# Включаем логирование
logging.basicConfig(level=logging.DEBUG)


def test_json_response():
    url = "https://kolybel.local/api/generate"

    # Тестовый запрос
    payload = {"model": "phi", "prompt": "Привет"}

    try:
        response = requests.post(url, json=payload, timeout=30, verify="ssl/cert.pem")

        print(f"\nRaw response text: {response.text[:500]}...")

        # Пробуем распарсить ответ по строкам
        for i, line in enumerate(response.text.split("\n")):
            if line.strip():  # пропускаем пустые строки
                try:
                    json.loads(line)
                    print(f"✅ Строка {i} успешно распарсена как JSON")
                except json.JSONDecodeError as e:
                    print(f"❌ Ошибка парсинга на строке {i}: {str(e)}")
                    print(f"Проблемная строка: {line[:100]}...")

    except Exception as e:
        logging.error(f"Ошибка запроса: {str(e)}", exc_info=True)


if __name__ == "__main__":
    test_json_response()
