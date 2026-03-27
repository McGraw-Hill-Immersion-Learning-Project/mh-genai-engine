#!/usr/bin/env python3
"""Dev CLI for the ingestion pipeline.

Run from repo root:
  python scripts/ingest.py run <filename>   Ingest a document from data/raw/
  python scripts/ingest.py run <file> -v    Verbose timings; add --library-logs for Docling/RapidOCR INFO
  python scripts/ingest.py list              List files in data/raw/
  python scripts/ingest.py --help            Show help and subcommands

Requires: .env with DATABASE_URL; VOYAGE_API_KEY (or EMBEDDING_PROVIDER=dev for local synthetic embeddings). Start DB: docker compose up db -d
"""

from __future__ import annotations

import asyncio
import logging
import sys
import time
from collections.abc import Callable
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


def _echo(msg: str, *, dim: bool = False) -> None:
    """All ingest progress on stderr so stdout stays clean for piping."""
    if dim:
        typer.echo(typer.style(msg, dim=True), err=True)
    else:
        typer.echo(msg, err=True)


def _quiet_library_loggers() -> None:
    """Hide Docling/RapidOCR INFO spam so pipeline steps stay readable."""
    for name in (
        "rapidocr",
        "RapidOCR",
        "docling",
        "docling_parse",
        "docling_core",
        "docling_ibm_models",
        "pypdfium2",
    ):
        logging.getLogger(name).setLevel(logging.WARNING)


def _get_service(
    settings: Settings,
    *,
    progress: Callable[[str], None] | None = None,
) -> IngestionService:
    storage = get_storage_provider(settings)
    embedder = get_embedding_provider(settings)
    vector_store = get_vector_store(settings)
    parser = DocumentParser(
        do_ocr=settings.do_ocr,
        do_table_structure=settings.do_table_structure,
        ocr_batch_size=settings.docling_ocr_batch_size,
        layout_batch_size=settings.docling_layout_batch_size,
        table_batch_size=settings.docling_table_batch_size,
        queue_max_size=settings.docling_queue_max_size,
    )
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
        progress=progress,
    )


async def _run_ingest(
    key: str,
    *,
    quiet: bool,
    library_logs: bool,
    verbose: bool,
) -> int:
    t0 = time.perf_counter()

    if not library_logs:
        _quiet_library_loggers()

    def _progress(msg: str) -> None:
        if not quiet:
            _echo(msg)

    if not quiet:
        _echo("")
        _echo(f"── ingest: {key}")
        _echo(
            "   read storage → parse (Docling) → chunk → embed → vector store",
            dim=True,
        )
        _echo("")

        _echo("[1/3] Loading settings...")
    settings = Settings()
    if not quiet:
        _echo(
            f"      EMBEDDING_PROVIDER={settings.embedding_provider}, "
            f"VECTOR_DB_PROVIDER={settings.vector_db_provider}, "
            f"DO_OCR={settings.do_ocr}"
        )
        _echo(
            f"      Docling: DO_TABLE_STRUCTURE={settings.do_table_structure}, "
            f"batch ocr/layout/table={settings.docling_ocr_batch_size}/"
            f"{settings.docling_layout_batch_size}/"
            f"{settings.docling_table_batch_size}, "
            f"queue_max={settings.docling_queue_max_size}",
            dim=True,
        )
        if verbose:
            _echo(f"      ({time.perf_counter() - t0:.1f}s)", dim=True)

        _echo("[2/3] Initializing providers (storage / embedder / vector store)...")
    t_providers = time.perf_counter()
    service = _get_service(settings, progress=_progress)
    if not quiet and verbose:
        _echo(f"      ({time.perf_counter() - t_providers:.1f}s)", dim=True)

    if not quiet:
        _echo("[3/3] Running pipeline (step details below)...")
        _echo("")
    t_pipe = time.perf_counter()
    count = await service.ingest(key)
    if not quiet:
        _echo("")
        _echo(f"Pipeline finished in {time.perf_counter() - t_pipe:.1f}s.")
        if verbose:
            _echo(f"Total elapsed {time.perf_counter() - t0:.1f}s.", dim=True)
    return count


@app.command()
def run(
    filename: str = typer.Argument(
        ...,
        help="File under data/raw/ to ingest (e.g. chapter1.pdf).",
    ),
    quiet: bool = typer.Option(
        False,
        "--quiet",
        "-q",
        help="Only print errors and the final summary line.",
    ),
    library_logs: bool = typer.Option(
        False,
        "--library-logs",
        help="Show Docling/RapidOCR/pypdfium INFO logs (hidden by default).",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Print timing for settings, providers, and total run.",
    ),
) -> None:
    """Run the full pipeline on a document: read -> parse -> chunk -> embed -> store."""
    key = filename.strip()
    try:
        count = asyncio.run(
            _run_ingest(
                key,
                quiet=quiet,
                library_logs=library_logs,
                verbose=verbose,
            )
        )
        typer.echo(
            typer.style(f"Done. Stored {count} chunks.", fg=typer.colors.GREEN),
            err=True,
        )
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
