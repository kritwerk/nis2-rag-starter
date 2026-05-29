"""Chroma-backed vector store with sentence-transformers embeddings."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol, cast

import structlog

from nis2_rag.ingest import Chunk

log = structlog.get_logger(__name__)


@dataclass(frozen=True)
class Hit:
    """A retrieval hit with all metadata needed for citation."""

    text: str
    source: str
    page: int
    score: float


class VectorStore(Protocol):
    def add(self, chunks: list[Chunk]) -> None: ...
    def query(self, text: str, *, top_k: int) -> list[Hit]: ...


class ChromaStore:
    """Thin wrapper around a persistent Chroma collection."""

    def __init__(
        self,
        *,
        persist_dir: Path,
        collection_name: str,
        embedding_model: str,
    ) -> None:
        # Imports are local to keep CLI startup fast and tests light.
        import chromadb
        from chromadb.utils import embedding_functions

        persist_dir.mkdir(parents=True, exist_ok=True)
        self._client = chromadb.PersistentClient(path=str(persist_dir))
        ef = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=embedding_model
        )
        self._collection = self._client.get_or_create_collection(
            name=collection_name,
            embedding_function=ef,  # type: ignore[arg-type]
            metadata={"hnsw:space": "cosine"},
        )

    def add(self, chunks: list[Chunk]) -> None:
        if not chunks:
            return
        ids = [f"{c.source}::{c.chunk_index}" for c in chunks]
        documents = [c.text for c in chunks]
        metadatas: list[dict[str, Any]] = [
            {"source": c.source, "page": c.page} for c in chunks
        ]
        self._collection.upsert(
            ids=ids,
            documents=documents,
            metadatas=cast(Any, metadatas),
        )
        log.info("chroma.upsert", count=len(chunks))

    def query(self, text: str, *, top_k: int) -> list[Hit]:
        result = cast(Any, self._collection.query(query_texts=[text], n_results=top_k))
        docs = (result.get("documents") or [[]])[0]
        metas = (result.get("metadatas") or [[]])[0]
        distances = (result.get("distances") or [[]])[0]
        hits: list[Hit] = []
        for doc, meta, dist in zip(docs, metas, distances, strict=False):
            hits.append(
                Hit(
                    text=doc,
                    source=str(meta.get("source", "?")),
                    page=int(meta.get("page", 0)),
                    score=1.0 - float(dist),  # cosine distance → similarity
                )
            )
        return hits
