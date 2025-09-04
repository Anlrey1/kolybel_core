# n8n_docs.py — загрузка, инкрементальная индексация и поиск по официальной документации n8n
"""Автоматически скачивает репозиторий n8n-io/n8n-docs, парсит Markdown и кладёт
фрагменты (чанки) в ChromaDB коллекцию `n8n_docs`.  
Особенности:
- Инкрементальное обновление: если хэш содержимого файла не изменился, документ
  не переиндексируется.
- Автоматический перевод русских запросов в английские без русской пост-обработки
  (используется generate_text_raw) + LRU-кэш переводов.
- CLI-режим: `python -m n8n_docs update` и `python -m n8n_docs search`.  
"""
from __future__ import annotations

import hashlib
import io
import json
import logging
import os
import re
import zipfile
from functools import lru_cache
from typing import Dict, Iterable, List, Optional

import requests

from memory_core import MemoryCore
from llm import generate_text_raw

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# === Константы ===
N8N_DOCS_ZIP_URL = "https://github.com/n8n-io/n8n-docs/archive/refs/heads/main.zip"
LOCAL_DOCS_DIR = os.path.join("docs", "n8n")
COLLECTION_NAME = "n8n_docs"

# === Regex для очистки Markdown ===
MD_FRONTMATTER_RE = re.compile(r"^---[\s\S]*?---\n", re.MULTILINE)
MD_CODEBLOCK_RE = re.compile(r"```[\s\S]*?```", re.MULTILINE)
MD_LINK_RE = re.compile(r"\[(.*?)\]\((.*?)\)")
MD_IMAGE_RE = re.compile(r"!\[[^\]]*\]\([^\)]*\)")

# == Утилиты файлов ==

def ensure_dirs() -> None:
    os.makedirs(LOCAL_DOCS_DIR, exist_ok=True)


def download_docs_zip() -> bytes:
    logger.info("⬇️  Скачивание официальной документации n8n (zip)…")
    resp = requests.get(N8N_DOCS_ZIP_URL, timeout=60)
    resp.raise_for_status()
    return resp.content


def extract_zip_to_dir(zip_bytes: bytes, target_dir: str) -> None:
    logger.info("📦 Распаковка архива…")
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        # Очистим папку назначения перед распаковкой
        for root, dirs, files in os.walk(target_dir, topdown=False):
            for file in files:
                try:
                    os.remove(os.path.join(root, file))
                except Exception:
                    pass
            for d in dirs:
                try:
                    os.rmdir(os.path.join(root, d))
                except Exception:
                    pass
        zf.extractall(target_dir)


def iter_markdown_files(root_dir: str) -> Iterable[str]:
    for root, _, files in os.walk(root_dir):
        for f in files:
            if f.lower().endswith(".md"):
                yield os.path.join(root, f)


def read_file_text(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except UnicodeDecodeError:
        with open(path, "r", encoding="latin-1") as f:
            return f.read()


# === Очистка и чанкирование ===

def clean_markdown(md: str) -> str:
    md = MD_FRONTMATTER_RE.sub("", md)
    md = MD_CODEBLOCK_RE.sub("", md)
    md = MD_LINK_RE.sub(lambda m: m.group(1), md)
    md = MD_IMAGE_RE.sub("", md)
    lines = [ln.strip() for ln in md.splitlines() if ln.strip()]
    return "\n".join(lines)


def chunk_text(text: str, max_chars: int = 1200, overlap: int = 150) -> List[str]:
    chunks: List[str] = []
    start = 0
    n = len(text)
    while start < n:
        end = min(n, start + max_chars)
        chunk = text[start:end]
        # расширим до ближайшего перевода строки, если позволяет лимит
        if end < n:
            nl = text.rfind("\n", start, end)
            if nl > start + 200:
                chunk = text[start:nl]
                end = nl
        chunks.append(chunk)
        start = max(end - overlap, end)
    return chunks


# === Перевод RU→EN с LRU-кэшем ===

@lru_cache(maxsize=256)
def _translate_ru_to_en_cached(text: str) -> str:
    prompt = (
        "Translate the following user phrase from Russian to English as literally as possible. "
        "Return ONLY the translated text, without quotes or comments.\n\n" + text
    )
    translated = generate_text_raw(prompt).strip() or text
    return translated


def ru_to_en(text: str) -> str:
    if not text:
        return text
    return _translate_ru_to_en_cached(text)


# === Класс доступа к знаниям ===

class N8nKnowledge:
    """Работа с индексом документации n8n."""

    def __init__(self, memory: Optional[MemoryCore] = None):
        self.memory = memory or MemoryCore()

    # == Индексация ==
    def update_index(self, limit_files: Optional[int] = None) -> Dict[str, int]:
        """Скачивает и переиндексирует документацию n8n.
        Делает инкрементальное обновление: для каждого Markdown файла считается
        SHA-1 хэш очищенного текста. Если такой хэш уже есть в коллекции — файл
        пропускается.
        """
        ensure_dirs()
        zip_bytes = download_docs_zip()
        extract_zip_to_dir(zip_bytes, LOCAL_DOCS_DIR)

        # корень, в котором распаковался архив (n8n-docs-main)
        root_dir = next(
            (
                os.path.join(LOCAL_DOCS_DIR, d)
                for d in os.listdir(LOCAL_DOCS_DIR)
                if os.path.isdir(os.path.join(LOCAL_DOCS_DIR, d)) and d.startswith("n8n-docs-")
            ),
            LOCAL_DOCS_DIR,
        )

        md_files = list(iter_markdown_files(root_dir))
        if limit_files:
            md_files = md_files[: limit_files]
        logger.info("📄 Найдено Markdown файлов: %s", len(md_files))

        skipped_files = 0
        added_chunks = 0
        for filepath in md_files:
            rel_path = os.path.relpath(filepath, root_dir)
            raw_md = read_file_text(filepath)
            cleaned = clean_markdown(raw_md)
            if not cleaned.strip():
                skipped_files += 1
                continue

            file_hash = hashlib.sha1(cleaned.encode("utf-8")).hexdigest()
            # Проверяем, есть ли уже документ с таким хэшем
            existing = self.memory.query_collection(
                COLLECTION_NAME,
                query="placeholder",  # сама строка не влияет на where
                n_results=1,
                where={"file_hash": {"$eq": file_hash}},
            )
            if existing:
                skipped_files += 1
                continue

            url_hint = f"https://docs.n8n.io/{rel_path.replace(os.sep, '/').replace('README.md','')}"
            for idx, chunk in enumerate(chunk_text(cleaned)):
                meta = {
                    "type": "n8n_doc",
                    "source_file": rel_path,
                    "chunk_index": idx,
                    "url": url_hint,
                    "file_hash": file_hash,
                }
                self.memory.store_in_collection(COLLECTION_NAME, chunk, metadata=meta)
                added_chunks += 1

        logger.info(
            "✅ Индексация завершена. Чанков добавлено: %s; файлов пропущено: %s",
            added_chunks,
            skipped_files,
        )
        return {
            "files_processed": len(md_files),
            "files_skipped": skipped_files,
            "chunks_added": added_chunks,
        }

    # == Поиск ==
    def search(self, query: str, n_results: int = 8) -> List[Dict]:
        # Определяем язык запроса (грубо)
        ru_chars = sum(1 for ch in query if "а" <= ch <= "я" or "А" <= ch <= "Я" or ch in "ёЁ")
        lat_chars = sum(1 for ch in query if "a" <= ch <= "z" or "A" <= ch <= "Z")
        if ru_chars > lat_chars:
            query_en = ru_to_en(query)
        else:
            query_en = query

        results = self.memory.query_collection(
            COLLECTION_NAME,
            query_en,
            n_results=n_results,
            where={"type": {"$eq": "n8n_doc"}},
        )

        for r in results:
            snippet = r.get("content", "")
            r["snippet"] = snippet[:500] + "…" if len(snippet) > 500 else snippet
        return results


# === CLI ===

def _cli() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="n8n docs indexer/search")
    sub = parser.add_subparsers(dest="cmd")

    p_upd = sub.add_parser("update", help="Download and (re)index n8n docs")
    p_upd.add_argument("--limit", type=int, default=None, help="Limit number of md files to index (debug)")

    p_search = sub.add_parser("search", help="Search in indexed n8n docs")
    p_search.add_argument("query", type=str, help="Query string (RU or EN)")
    p_search.add_argument("--k", type=int, default=8, help="Number of results to return")

    args = parser.parse_args()
    kn = N8nKnowledge()

    if args.cmd == "update":
        stats = kn.update_index(limit_files=args.limit)
        print(json.dumps(stats, ensure_ascii=False, indent=2))
    elif args.cmd == "search":
        hits = kn.search(args.query, n_results=args.k)
        print(json.dumps(hits, ensure_ascii=False, indent=2))
    else:
        parser.print_help()


if __name__ == "__main__":
    _cli()
