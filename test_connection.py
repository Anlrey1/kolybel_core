import requests

try:
    response = requests.post(
        "https://kolybel.local/api/generate",
        json={"model": "phi", "prompt": "Привет"},
        timeout=20,
        verify="ssl/cert.pem",
    )
    print(f"Status: {response.status_code}")
    print(f"Body: {response.text[:200]}...")
except Exception as e:
    print(f"Ошибка: {str(e)}")
