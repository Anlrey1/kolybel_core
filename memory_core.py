# memory_core.py — надёжная инициализация Chroma + эмбеддинги
import os
import logging
from datetime import datetime
from typing import Dict, List, Optional

from sentence_transformers import SentenceTransformer
from chromadb import PersistentClient
from chromadb.config import Settings

from config import CRADLE_MEMORY_DIR, MODELS_CACHE_DIR

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class MemoryCore:
    def __init__(self):
        self._init_embedder()
        self._init_chroma()

    def _init_embedder(self):
        try:
            self.embedder = SentenceTransformer(
                "all-MiniLM-L6-v2",
                cache_folder=MODELS_CACHE_DIR,
                device="cpu",
            )
        except Exception as e:
            logger.error(f"Ошибка загрузки SentenceTransformer: {e}")
            logger.warning("Используем заглушку для embedder'а")
            # Создаем заглушку для embedder'а
            class EmbedderMock:
                def encode(self, texts):
                    import numpy as np
                    if isinstance(texts, list):
                        return np.array([[0.0] * 384 for _ in texts])
                    else:
                        return np.array([0.0] * 384)
            self.embedder = EmbedderMock()

    def _init_chroma(self):
        try:
            # Используем новую директорию для базы данных
            db_dir = CRADLE_MEMORY_DIR + "_new"

            self.client = PersistentClient(
                settings=Settings(
                    persist_directory=db_dir,
                    allow_reset=True,
                    anonymized_telemetry=False,
                    is_persistent=True,
                )
            )
            self.collection = self.client.get_or_create_collection(
                name="cradle_v5",
                metadata={"hnsw:space": "cosine", "description": "Основное хранилище Колыбели"},
            )
            logger.info(f"ChromaDB инициализирован в новой директории: {db_dir}")
        except Exception as e:
            logger.error(f"ChromaDB init error: {e}")
            logger.warning("Используем заглушку для ChromaDB")
            # Создаем заглушку для ChromaDB
            class ChromaMock:
                def add(self, *args, **kwargs):
                    pass
                def query(self, *args, **kwargs):
                    return {"documents": [], "metadatas": [], "ids": []}
            self.collection = ChromaMock()

    def store(self, document: str, metadata: Optional[Dict] = None) -> str:
        emb = self.embedder.encode(document).tolist()
        doc_id = f"doc_{datetime.now().timestamp()}"
        self.collection.add(
            documents=[document],
            embeddings=[emb],
            ids=[doc_id],
            metadatas=[metadata] if metadata else None,
        )
        return doc_id

    def get_similar(self, query: str, n_results: int = 5, filter_type: Optional[str] = None) -> List[Dict]:
        qv = self.embedder.encode(query).tolist()
        res = self.collection.query(
            query_embeddings=[qv],
            n_results=max(1, n_results),
            include=["documents", "metadatas"],
        )
        docs = res.get("documents", [[]])[0]
        metas = res.get("metadatas", [[]])[0]
        out = [{"content": d, "metadata": (m or {})} for d, m in zip(docs, metas)]
        if filter_type:
            out = [r for r in out if filter_type in r.get("metadata", {}).get("type", "")]
        return out

    # === Расширение: поддержка именованных коллекций для разных доменов знаний ===
    def get_or_create_collection(self, name: str, metadata: Optional[Dict] = None):
        """Возвращает или создаёт коллекцию по имени (например, 'n8n_docs')."""
        md = {"hnsw:space": "cosine"}
        if metadata:
            md.update(metadata)
        return self.client.get_or_create_collection(name=name, metadata=md)

    def store_in_collection(
        self,
        collection_name: str,
        document: str,
        metadata: Optional[Dict] = None,
        doc_id: Optional[str] = None,
    ) -> str:
        """Добавляет документ в указанную коллекцию."""
        col = self.get_or_create_collection(collection_name)
        emb = self.embedder.encode(document).tolist()
        _id = doc_id or f"{collection_name}_{datetime.now().timestamp()}"
        col.add(
            documents=[document],
            embeddings=[emb],
            ids=[_id],
            metadatas=[metadata] if metadata else None,
        )
        return _id

    def query_collection(
        self,
        collection_name: str,
        query: str,
        n_results: int = 5,
        where: Optional[Dict] = None,
    ) -> List[Dict]:
        """Ищет похожие документы в указанной коллекции."""
        col = self.get_or_create_collection(collection_name)
        qv = self.embedder.encode(query).tolist()
        res = col.query(
            query_embeddings=[qv],
            n_results=max(1, n_results),
            include=["documents", "metadatas"],
            where=where,
        )
        docs = res.get("documents", [[]])[0]
        metas = res.get("metadatas", [[]])[0]
        return [{"content": d, "metadata": (m or {})} for d, m in zip(docs, metas)]

    def train_on_memories(self, threshold: float = 0.7):
        # Подготовка обучающих примеров из удачных ответов
        successful = self.get_similar("successful response", n_results=10, filter_type="response")
        data = "\n".join(f"[example]\n{it['content']}\n[/example]" for it in successful)
        os.makedirs("training_workflows", exist_ok=True)
        with open("training_workflows/agent_prompt_examples.txt", "w", encoding="utf-8") as f:
            f.write(data)
        self.store(
            f"Обучение завершено. Примеры: {len(successful)}",
            {"type": "training", "count": len(successful), "timestamp": datetime.now().isoformat()},
        )
