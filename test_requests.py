import requests


def test_request_options():
    tests = [
        {"stream": True, "temperature": 0.7},
        {"stream": False, "temperature": 0.5},
        {"max_tokens": 100, "temperature": 0.8},
    ]

    for i, params in enumerate(tests):
        print(f"\nТест #{i+1} с параметрами: {params}")
        try:
            response = requests.post(
                "https://kolybel.local/api/generate",
                json={"model": "phi", "prompt": "Привет", **params},
                timeout=30,
                verify="ssl/cert.pem",
            )

            print(f"Status code: {response.status_code}")
            print(f"Response length: {len(response.text)}")

        except Exception as e:
            print(f"❌ Ошибка: {str(e)}")


if __name__ == "__main__":
    test_request_options()
