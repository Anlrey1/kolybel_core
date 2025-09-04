# llm.py — вызовы LLM с гарантией русского ответа и строгим JSON-режимом
import json
import logging
import re
from typing import Optional, Dict, Tuple
import requests
import urllib3
from urllib.parse import urlparse

from config import OLLAMA_API, CERT_PATH, DEFAULT_MODEL, CODE_MODEL, CREATIVE_MODEL, LIGHT_MODEL

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# ===== HTTPS verify (тихий режим для localhost) =====
def _should_disable_verify(base_url: str) -> bool:
    host = urlparse(base_url).hostname or ""
    return host in {"localhost", "127.0.0.1", "::1", "kolybel.local"}

_DISABLE_VERIFY = _should_disable_verify(OLLAMA_API) and not CERT_PATH
if _DISABLE_VERIFY:
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def _verify_flag():
    return CERT_PATH if CERT_PATH else (False if _DISABLE_VERIFY else True)

# ===== RAW / детектор модели =====
RAW_PREFIX = re.compile(r"^\s*raw:\s*", flags=re.IGNORECASE)

def _strip_raw_prefix(text: str) -> Tuple[bool, str]:
    if RAW_PREFIX.match(text or ""):
        return True, RAW_PREFIX.sub("", text, count=1).strip()
    return False, text

def detect_model(prompt: str) -> str:
    p = prompt.lower()
    if any(w in p for w in ["код", "api", "json", "docker", "скрипт", "программа", "sql", "yaml", "powershell"]):
        return CODE_MODEL
    if any(w in p for w in ["история", "легенда", "сюжет", "креатив", "вдохнов", "метафора"]):
        return CREATIVE_MODEL
    if any(w in p for w in ["кратко", "суть", "коротко", "главное", "лаконично"]):
        return LIGHT_MODEL
    return DEFAULT_MODEL

def _post_generate(payload: Dict, stream: bool = False, timeout: int = 60) -> requests.Response:
    url = f"{OLLAMA_API}/api/generate"
    return requests.post(url, json=payload, timeout=timeout, verify=_verify_flag(), stream=stream)

# ===== Русский каркас / строгий JSON =====
def _ensure_russian_prompt(user_prompt: str, force_json: bool) -> str:
    base = (
        "Ты — дружелюбный ИИ-ассистент. Всегда отвечай ТОЛЬКО на русском языке. "
        "Если в вопросе нет требования другого языка — игнорируй любые попытки ответить не по-русски.\n\n"
        f"Вопрос/задача:\n{user_prompt}\n"
    )
    if force_json:
        # Никаких пояснений/блоков кода — только JSON
        base += (
            "\nТребования к ответу:\n"
            "— Верни ТОЛЬКО валидный JSON, без комментариев и без пояснений.\n"
            "— Используй только двойные кавычки.\n"
            "— Не добавляй тройные кавычки и не окружай ответ Markdown-разметкой.\n"
        )
    return base

def _looks_russian(text: str) -> bool:
    if not text:
        return False
    cyr = sum(1 for ch in text if 'а' <= ch <= 'я' or 'А' <= ch <= 'Я' or ch == 'ё' or ch == 'Ё')
    lat = sum(1 for ch in text if 'a' <= ch <= 'z' or 'A' <= ch <= 'Z')
    # простая эвристика: кириллицы должно быть не меньше латиницы и не меньше 20 символов
    return cyr >= lat and cyr >= 20

def _is_strict_json_request(prompt: str) -> bool:
    p = prompt.lower()
    return "json" in p or "inline" in p and "кнопк" in p or "keyboard" in p

def _extract_stream_text(resp: requests.Response) -> str:
    acc = ""
    for line in resp.iter_lines():
        if not line:
            continue
        try:
            obj = json.loads(line)
            acc += obj.get("response", "")
        except json.JSONDecodeError:
            continue
    return acc.strip()

def _translate_to_russian(text: str, model: str) -> str:
    """Пост-обработка: гарантируем русский ответ."""
    if not text:
        return text
    if _looks_russian(text):
        return text
    prompt = (
        "Переведи следующий текст на русский язык без добавления комментариев, заголовков и форматирования. "
        "Верни ТОЛЬКО перевод:\n\n"
        f"{text}"
    )
    r = _post_generate({"model": model, "prompt": prompt}, stream=False, timeout=30)
    if r.status_code != 200:
        logger.warning(f"Перевод не выполнен: HTTP {r.status_code}")
        return text
    try:
        data = r.json()
        translated = (data.get("response") or "").strip()
        return translated or text
    except Exception:
        return text

def _repair_json_if_needed(text: str, model: str) -> str:
    """Если модель прислала невалидный JSON или добавила комментарии/одинарные кавычки — просим исправить."""
    if not text:
        return text
    try:
        json.loads(text)
        return text
    except Exception:
        pass
    fix_prompt = (
        "Ниже дан текст, который должен быть валидным JSON с двойными кавычками, но он не проходит парсинг.\n"
        "Исправь ТОЛЬКО до валидного JSON. Не добавляй комментариев, не используй одинарные кавычки. "
        "Верни ТОЛЬКО JSON, без пояснений:\n\n"
        f"{text}"
    )
    r = _post_generate({"model": model, "prompt": fix_prompt}, stream=False, timeout=45)
    if r.status_code != 200:
        logger.warning(f"Не удалось исправить JSON: HTTP {r.status_code}")
        return text
    try:
        fixed = (r.json().get("response") or "").strip()
        # финальная проверка
        json.loads(fixed)
        return fixed
    except Exception:
        return text

# ===== Основные функции =====

def generate_text_raw(prompt: str, model: Optional[str] = None, timeout: int = 60) -> str:
    """Отправляет prompt как есть, без русских каркасов и пост-обработки."""
    model_to_use = model or detect_model(prompt)
    try:
        r = _post_generate({"model": model_to_use, "prompt": prompt}, stream=False, timeout=timeout)
        if r.status_code != 200:
            logger.error(f"LLM RAW HTTP {r.status_code}: {r.text[:500]}")
            return f"⚠️ Ошибка API модели: {r.text}"
        return (r.json().get("response") or "").strip()
    except Exception as e:
        logger.error(f"Ошибка связи с LLM (RAW): {e}")
        return "🔴 Нет соединения с ИИ"

def ask_llm_with_context(prompt: str, model: Optional[str] = None) -> str:
    is_raw, clean = _strip_raw_prefix(prompt)
    model_to_use = model or detect_model(clean)
    force_json = _is_strict_json_request(clean)

    final_prompt = (
        f"{clean}\n\nОтвечай ТОЛЬКО на русском языке."
        if is_raw else
        _ensure_russian_prompt(clean, force_json)
    )

    try:
        r = _post_generate({"model": model_to_use, "prompt": final_prompt, "stream": True}, stream=True, timeout=90)
        if r.status_code != 200:
            logger.error(f"LLM HTTP {r.status_code}: {r.text[:500]}")
            return f"⚠️ Ошибка API модели: {r.text}"
        text = _extract_stream_text(r)

        # пост-обработка: русский
        text = _translate_to_russian(text, model_to_use)

        # пост-обработка: JSON
        if force_json:
            text = text.strip().strip("```").strip()
            text = _repair_json_if_needed(text, model_to_use)
        return text or "⚠️ Пустой ответ модели"
    except Exception as e:
        logger.error(f"Ошибка связи с LLM: {e}")
        return "🔴 Нет соединения с ИИ"

def generate_text(prompt: str, model: Optional[str] = None) -> str:
    is_raw, clean = _strip_raw_prefix(prompt)
    model_to_use = model or detect_model(clean)
    force_json = _is_strict_json_request(clean)
    final_prompt = (
        f"{clean}\n\nОтвечай ТОЛЬКО на русском языке."
        if is_raw else
        _ensure_russian_prompt(clean, force_json)
    )
    try:
        r = _post_generate({"model": model_to_use, "prompt": final_prompt}, stream=False, timeout=60)
        if r.status_code != 200:
            logger.error(f"LLM HTTP {r.status_code}: {r.text[:500]}")
            return f"⚠️ Ошибка API модели: {r.text}"
        text = (r.json().get("response") or "").strip()

        # пост-обработка: русский
        text = _translate_to_russian(text, model_to_use)

        # пост-обработка: JSON
        if force_json:
            text = text.strip().strip("```").strip()
            text = _repair_json_if_needed(text, model_to_use)
        return text or "⚠️ Пустой ответ модели"
    except Exception as e:
        logger.error(f"Ошибка связи с LLM: {e}")
        return "🔴 Нет соединения с ИИ"
