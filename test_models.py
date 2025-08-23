import requests
import json

MODELS = ["phi", "mistral", "nous-hermes", "deepseek-coder"]


def test_model(model_name):
    try:
        response = requests.post(
            "https://kolybel.local/api/generate",
            json={"model": model_name, "prompt": "Привет"},
            timeout=30,
            verify="ssl/cert.pem",
        )

        print(f"\nТест модели {model_name}:")
        print(f"Status code: {response.status_code}")

        if response.status_code == 200:
            print(f"Первые 100 символов ответа: {response.text[:100]}...")

            # Попытка распарсить JSON
            try:
                lines = [l for l in response.text.split("\n") if l.strip()]
                print(f"Всего строк: {len(lines)}")
                print("Первая строка:", lines[0][:100])

                # Пробуем распарсить первую строку
                first_json = json.loads(lines[0])
                print("\nПоля первого JSON-объекта:", first_json.keys())

            except json.JSONDecodeError as e:
                print("❌ Ошибка JSON-декодирования:", str(e))

    except Exception as e:
        print(f"❌ Ошибка для модели {model_name}:", str(e))


if __name__ == "__main__":
    for model in MODELS:
        test_model(model)
