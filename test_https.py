import requests

# URL вашего Ollama API через Nginx
url = "https://kolybel.local/api/generate"

# Путь к вашему самоподписанному сертификату
cert_path = "C:/Users/Andrew/kolybel_core/ssl/cert.pem"

try:
    # Отправляем POST-запрос к ИИ
    response = requests.post(
        url,
        json={"model": "phi", "prompt": "Привет"},
        verify=cert_path,  # Указываем, что использовать именно этот сертификат
        timeout=20,
    )

    print("✅ Сервер ответил:")
    print("Код статуса:", response.status_code)
    print("Тело ответа:")
    print(response.text)

except requests.exceptions.SSLError as ssl_err:
    print("❌ Ошибка SSL:")
    print(ssl_err)

except requests.exceptions.ConnectionError as conn_err:
    print("❌ Ошибка подключения:")
    print(conn_err)

except Exception as e:
    print("❌ Непредвиденная ошибка:")
    print(e)
