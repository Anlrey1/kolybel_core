from cryptography import x509
from cryptography.x509.oid import NameOID, ExtensionOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from datetime import datetime, timedelta
import os
import ipaddress

# Генерация ключа
private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

# Создание самоподписанного сертификата с SAN
subject = issuer = x509.Name(
    [
        x509.NameAttribute(NameOID.COMMON_NAME, "kolybel.local"),
    ]
)

# Создаем расширение SAN с DNS-именами и IP-адресами
san_builder = x509.SubjectAlternativeName(
    [
        x509.DNSName("kolybel.local"),
        x509.DNSName("localhost"),
        x509.IPAddress(ipaddress.IPv4Address("127.0.0.1")),
        x509.IPAddress(ipaddress.IPv6Address("::1")),
    ]
)

cert = (
    x509.CertificateBuilder()
    .subject_name(subject)
    .issuer_name(issuer)
    .public_key(private_key.public_key())
    .serial_number(x509.random_serial_number())
    .not_valid_before(datetime.utcnow())
    .not_valid_after(datetime.utcnow() + timedelta(days=365))
    .add_extension(
        san_builder,
        critical=False,
    )
    .add_extension(
        x509.BasicConstraints(ca=True, path_length=None),
        critical=True,
    )
    .sign(private_key, hashes.SHA256(), None)
)

# Сохранение файлов
os.makedirs("ssl", exist_ok=True)

with open("ssl/cert.pem", "wb") as f:
    f.write(cert.public_bytes(serialization.Encoding.PEM))

with open("ssl/key.pem", "wb") as f:
    f.write(
        private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )

print("✅ Сертификат с SAN создан:")
print(" - ssl/cert.pem")
print(" - ssl/key.pem")
