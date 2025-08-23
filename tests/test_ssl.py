# tests/test_ssl.py
import os
import pytest
import sys
from pathlib import Path

# Добавляем корень проекта в PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent))

from memory_core import MemoryCore


def test_ssl_with_existing_certificates():
    """Проверка работы с существующими сертификатами"""
    # Убедимся, что папка ssl/ существует
    assert os.path.exists("ssl"), "Папка ssl/ не найдена"
    assert os.path.exists("ssl/cert.pem"), "Файл cert.pem отсутствует"
    assert os.path.exists("ssl/key.pem"), "Файл key.pem отсутствует"

    # Инициализация MemoryCore (должна пройти без ошибок)
    memory = MemoryCore()
    assert memory.ssl_context is not None
