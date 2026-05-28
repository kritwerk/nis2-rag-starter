"""Document loading, chunking, and ingestion into Chroma."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import structlog
from pypdf import PdfReader

log = structlog.get_logger(__name__)


@dataclass(frozen=True)
class Chunk:
    """One indexed chunk with metadata for traceable citations."""

    text: str
    source: str
    page: int
    chunk_index: int


def load_document(path: Path) -> list[tuple[int, str]]:
    """Return a list of (page_number, text) tuples.

    Supports `.pdf` (page-aware) and `.txt` / `.md` (single 'page').
    Page numbers are 1-based for human-readable citations.
    """
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        reader = PdfReader(str(path))
        return [(i + 1, page.extract_text() or "") for i, page in enumerate(reader.pages)]
    if suffix in {".txt", ".md"}:
        return [(1, path.read_text(encoding="utf-8"))]
    raise ValueError(f"Unsupported file type: {suffix}. Use .pdf, .txt, or .md.")


def chunk_text(
    text: str,
    *,
    source: str,
    page: int,
    chunk_size: int,
    chunk_overlap: int,
    start_index: int = 0,
) -> list[Chunk]:
    """Split `text` into overlapping chunks of approximately `chunk_size` chars."""
    if chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap must be smaller than chunk_size")

    text = text.strip()
    if not text:
        return []

    step = chunk_size - chunk_overlap
    chunks: list[Chunk] = []
    pos = 0
    idx = start_index
    while pos < len(text):
        piece = text[pos : pos + chunk_size].strip()
        if piece:
            chunks.append(Chunk(text=piece, source=source, page=page, chunk_index=idx))
            idx += 1
        pos += step
    return chunks


def build_chunks(
    pages: list[tuple[int, str]],
    *,
    source: str,
    chunk_size: int,
    chunk_overlap: int,
) -> list[Chunk]:
    """Chunk all pages and return a flat, sequentially indexed list."""
    chunks: list[Chunk] = []
    for page_number, page_text in pages:
        chunks.extend(
            chunk_text(
                page_text,
                source=source,
                page=page_number,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                start_index=len(chunks),
            )
        )
    return chunks


def ingest_path(path: Path, *, chunk_size: int, chunk_overlap: int) -> list[Chunk]:
    """Load + chunk a single document path."""
    log.info("ingest.load", path=str(path))
    pages = load_document(path)
    chunks = build_chunks(
        pages,
        source=path.name,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    log.info("ingest.chunks", count=len(chunks), source=path.name)
    return chunks
