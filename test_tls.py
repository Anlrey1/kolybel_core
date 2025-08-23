import httpx

client = httpx.Client(verify=False, timeout=20)

try:
    response = client.post(
        "https://host.docker.internal/api/generate",
        json={"model": "mistral", "prompt": "Привет"},
    )
    print("✅ Ответ:", response.status_code)
    print(response.text)
except Exception as e:
    print("❌ Ошибка:", str(e))
