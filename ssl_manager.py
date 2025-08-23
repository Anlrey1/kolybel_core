# ssl_manager.py
import os
import logging
from datetime import datetime, timedelta
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID


class SSLCertManager:
    @staticmethod
    def generate_self_signed_cert(cert_path: str, key_path: str):
        """Генерация самоподписанного сертификата"""
        # ... (код генерации из предыдущего ответа)

    @staticmethod
    def check_expiry(cert_path: str) -> int:
        """Проверка срока действия сертификата"""
        # ... (код проверки из предыдущего ответа)

    @staticmethod
    def init_ssl_context(cert_path: str) -> ssl.SSLContext:
        """Создание SSL-контекста"""
        context = ssl.create_default_context()
        context.load_verify_locations(cafile=cert_path)
        return context
