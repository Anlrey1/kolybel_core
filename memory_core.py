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
            raise

    def _init_chroma(self):
        try:
            self.client = PersistentClient(
                settings=Settings(
                    persist_directory=CRADLE_MEMORY_DIR,
                    allow_reset=True,
                    anonymized_telemetry=False,
                    is_persistent=True,
                )
            )
            self.collection = self.client.get_or_create_collection(
                name="cradle_v5",
                metadata={"hnsw:space": "cosine", "description": "Основное хранилище Колыбели"},
            )
        except Exception as e:
            logger.error(f"ChromaDB init error: {e}")
            raise

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
