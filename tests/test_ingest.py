from nis2_rag.ingest import build_chunks, chunk_text


def test_chunk_text_splits_with_overlap() -> None:
    text = "a" * 1000
    chunks = chunk_text(text, source="x.md", page=1, chunk_size=400, chunk_overlap=50)
    assert len(chunks) >= 3
    assert all(c.source == "x.md" and c.page == 1 for c in chunks)
    # Indices are contiguous starting at 0
    assert [c.chunk_index for c in chunks] == list(range(len(chunks)))


def test_chunk_text_empty_returns_empty() -> None:
    assert chunk_text("   ", source="x", page=1, chunk_size=100, chunk_overlap=10) == []


def test_build_chunks_assigns_global_indices() -> None:
    pages = [(1, "alpha " * 200), (2, "beta " * 200)]
    chunks = build_chunks(pages, source="doc.pdf", chunk_size=300, chunk_overlap=30)
    # All sequentially numbered
    assert [c.chunk_index for c in chunks] == list(range(len(chunks)))
    # Both pages represented
    pages_seen = {c.page for c in chunks}
    assert pages_seen == {1, 2}
