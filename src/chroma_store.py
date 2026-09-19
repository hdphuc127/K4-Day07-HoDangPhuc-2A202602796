"""Persistent vector store backed by ChromaDB.

Kept separate from `src/store.py::EmbeddingStore` on purpose: that class is
pytest-covered and the lab explicitly requires it to stay in-memory only (see
CHECKPOINT 5 notes on the `_use_chroma` trap). This module is the demo-only,
optional persistence layer for `cli_demo.py` — not graded, not imported by
tests.

Data is written to disk under `persist_directory` and survives across
process restarts, so you only pay the embedding cost once per corpus.
"""
from __future__ import annotations

import os
from typing import Any, Callable

from .embeddings import _mock_embed
from .models import Document

DEFAULT_PERSIST_DIR = "./chroma_data"


class ChromaEmbeddingStore:
    """Same read/write surface as EmbeddingStore's search methods, backed by Chroma."""

    def __init__(
        self,
        collection_name: str = "documents",
        embedding_fn: Callable[[str], list[float]] | None = None,
        persist_directory: str | None = None,
    ) -> None:
        import chromadb

        self._embedding_fn = embedding_fn or _mock_embed
        self._persist_directory = persist_directory or os.getenv("CHROMA_PERSIST_DIR", DEFAULT_PERSIST_DIR)
        self._client = chromadb.PersistentClient(path=self._persist_directory)
        self._collection = self._client.get_or_create_collection(name=collection_name)

    def get_collection_size(self) -> int:
        return self._collection.count()

    def add_documents(self, docs: list[Document]) -> None:
        """Embed + upsert. Upsert (not add) so re-running the script is idempotent."""
        if not docs:
            return
        ids = [doc.id for doc in docs]
        contents = [doc.content for doc in docs]
        embeddings = [self._embedding_fn(doc.content) for doc in docs]
        metadatas = []
        for doc in docs:
            metadata = dict(doc.metadata)
            metadata.setdefault("doc_id", doc.id)
            metadatas.append(metadata)
        self._collection.upsert(ids=ids, documents=contents, embeddings=embeddings, metadatas=metadatas)

    def _to_records(self, result: dict[str, Any]) -> list[dict[str, Any]]:
        records: list[dict[str, Any]] = []
        ids = result.get("ids") or [[]]
        docs = result.get("documents") or [[]]
        metas = result.get("metadatas") or [[]]
        dists = result.get("distances") or [[]]
        for id_, content, metadata, distance in zip(ids[0], docs[0], metas[0], dists[0]):
            # Chroma's default space is squared L2 on raw embeddings; convert to a
            # similarity-style score so it reads the same as EmbeddingStore's dot product.
            records.append({
                "id": id_,
                "content": content,
                "metadata": dict(metadata),
                "score": 1.0 / (1.0 + distance),
            })
        return records

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        return self.search_with_filter(query, top_k=top_k, metadata_filter=None)

    def search_with_filter(self, query: str, top_k: int = 3, metadata_filter: dict | None = None) -> list[dict]:
        query_embedding = self._embedding_fn(query)
        where = metadata_filter if metadata_filter else None
        result = self._collection.query(query_embeddings=[query_embedding], n_results=top_k, where=where)
        return self._to_records(result)

    def delete_document(self, doc_id: str) -> bool:
        existing = self._collection.get(where={"doc_id": doc_id})
        ids = existing.get("ids") or []
        if not ids:
            return False
        self._collection.delete(ids=ids)
        return True
