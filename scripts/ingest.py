#!/usr/bin/env python3
"""Dev CLI for the ingestion pipeline.

Run from repo root:
  python scripts/ingest.py run <filename>   Ingest a document from data/raw/
  python scripts/ingest.py list              List files in data/raw/
  python scripts/ingest.py --help            Show help and subcommands

Requires: .env with DATABASE_URL; VOYAGE_API_KEY (or EMBEDDING_PROVIDER=dev for local synthetic embeddings). Start DB: docker compose up db -d
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

if __name__ == "__main__":
    _root = Path(__file__).resolve().parent.parent
    if str(_root) not in sys.path:
        sys.path.insert(0, str(_root))

import typer
from app.config import Settings
from app.core.ingestion.chunker import TextChunker
from app.core.ingestion.parser import DocumentParser
from app.core.ingestion.service import IngestionService
from app.providers import (
    get_embedding_provider,
    get_storage_provider,
    get_vector_store,
)

app = typer.Typer(
    name="ingest",
    help="Ingestion pipeline CLI: run the pipeline on documents in data/raw/ or list available files. Use 'run <file>' or 'list'.",
)


def _get_service(settings: Settings) -> IngestionService:
    storage = get_storage_provider(settings)
    embedder = get_embedding_provider(settings)
    vector_store = get_vector_store(settings)
    parser = DocumentParser()
    chunker = TextChunker(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
    )
    return IngestionService(
        storage=storage,
        parser=parser,
        chunker=chunker,
        embedder=embedder,
        vector_store=vector_store,
        batch_size=settings.embedding_batch_size,
        batch_delay_seconds=settings.embedding_batch_delay_seconds,
        max_chunks=settings.dev_max_chunks if settings.embedding_provider.lower() == "dev" else 0,
    )


async def _run_ingest(key: str) -> int:
    # Load settings and construct the ingestion service step by step so we can
    # surface where things might hang during local runs.
    typer.echo("Loading settings...", err=True)
    settings = Settings()
    typer.echo(
        f"Settings loaded (EMBEDDING_PROVIDER={settings.embedding_provider}, "
        f"VECTOR_DB_PROVIDER={settings.vector_db_provider}).",
        err=True,
    )

    typer.echo("Initializing providers (storage/embedder/vector store)...", err=True)
    service = _get_service(settings)
    typer.echo("Providers initialized. Starting ingestion pipeline...", err=True)

    count = await service.ingest(key)
    typer.echo("Ingestion pipeline finished.", err=True)
    return count


@app.command()
def run(
    filename: str = typer.Argument(
        ...,
        help="File under data/raw/ to ingest (e.g. chapter1.pdf).",
    ),
) -> None:
    """Run the full pipeline on a document: read -> parse -> chunk -> embed -> store."""
    key = filename.strip()
    typer.echo(f"Ingesting {key} ...")
    try:
        count = asyncio.run(_run_ingest(key))
        typer.echo(typer.style(f"Done. Stored {count} chunks.", fg=typer.colors.GREEN))
    except FileNotFoundError as e:
        typer.echo(typer.style(str(e), fg=typer.colors.RED), err=True)
        raise typer.Exit(1)
    except Exception as e:
        typer.echo(typer.style(f"Error: {e}", fg=typer.colors.RED), err=True)
        raise typer.Exit(1)


@app.command("list")
def list_cmd(
    prefix: str = typer.Option(
        "",
        "--prefix",
        "-p",
        help="Filter listed files by prefix.",
    ),
) -> None:
    """List files in data/raw/ that can be ingested."""
    async def _list() -> list[str]:
        settings = Settings()
        storage = get_storage_provider(settings)
        return await storage.list_files(prefix=prefix)

    files = asyncio.run(_list())
    if not files:
        typer.echo("No files in data/raw. Add a PDF and try again.")
        return
    typer.echo(f"Files in data/raw (prefix={prefix!r}):")
    for f in files:
        typer.echo(f"  {f}")


if __name__ == "__main__":
    app()
