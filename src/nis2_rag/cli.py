"""Command-line interface for nis2-rag."""
from __future__ import annotations

import logging
from pathlib import Path

import structlog
import typer
from rich.console import Console
from rich.panel import Panel

from nis2_rag.config import Settings, load_settings
from nis2_rag.ingest import ingest_path
from nis2_rag.qa import answer_question
from nis2_rag.store import ChromaStore

app = typer.Typer(
    add_completion=False,
    no_args_is_help=True,
    help="NIS2-Policies durchsuchbar machen — mit Quellen-Referenzen.",
)
console = Console()


def _configure_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.WARNING
    logging.basicConfig(level=level, format="%(message)s")
    structlog.configure(
        wrapper_class=structlog.make_filtering_bound_logger(level),
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer(colors=True),
        ],
    )


def _build_store(settings: Settings) -> ChromaStore:
    return ChromaStore(
        persist_dir=settings.chroma_dir,
        collection_name=settings.collection_name,
        embedding_model=settings.embedding_model,
    )


@app.command()
def ingest(
    path: Path = typer.Argument(..., exists=True, readable=True, help="PDF, TXT oder MD"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Debug-Logs."),
) -> None:
    """Dokument in den Vektor-Index aufnehmen."""
    _configure_logging(verbose)
    settings = load_settings()
    chunks = ingest_path(
        path,
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
    )
    store = _build_store(settings)
    store.add(chunks)
    console.print(
        f"[green]✓[/green] {len(chunks)} Chunks aus [bold]{path.name}[/bold] indiziert "
        f"in [italic]{settings.chroma_dir}[/italic]."
    )


@app.command()
def ask(
    question: str = typer.Argument(..., help="Deine Frage in natürlicher Sprache."),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Debug-Logs."),
) -> None:
    """Eine Frage gegen den Index stellen — Antwort enthält Quellen."""
    _configure_logging(verbose)
    settings = load_settings()
    store = _build_store(settings)
    hits = store.query(question, top_k=settings.top_k)

    if not hits:
        console.print("[yellow]Keine Treffer im Index. Bitte zuerst `ingest` ausführen.[/yellow]")
        raise typer.Exit(code=1)

    answer = answer_question(question, hits, settings)
    console.print(Panel.fit(answer.text, title="Antwort", border_style="cyan"))

    console.print("\n[bold]Quellen-Auszüge:[/bold]")
    for i, hit in enumerate(answer.citations, start=1):
        excerpt = hit.text[:240].replace("\n", " ")
        console.print(
            f"  [dim]{i}.[/dim] {hit.source}, Seite {hit.page} "
            f"[dim](score {hit.score:.2f})[/dim]\n     {excerpt}…"
        )


@app.command()
def reset() -> None:
    """Vektor-Index löschen (Chroma-Verzeichnis)."""
    settings = load_settings()
    if not settings.chroma_dir.exists():
        console.print("[yellow]Nichts zu löschen.[/yellow]")
        return
    import shutil

    shutil.rmtree(settings.chroma_dir)
    console.print(f"[green]✓[/green] {settings.chroma_dir} gelöscht.")


if __name__ == "__main__":
    app()
