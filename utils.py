"""Shared utilities for the repo (importable from anywhere).

Keep this module lightweight and dependency-free so it is safe to import from
core application code, scripts, and tests.
"""

from __future__ import annotations

import logging
import re
import hashlib


def get_logger(name: str) -> logging.Logger:
    """Return a module-scoped logger.

    Logging configuration (handlers/levels/formatters) should be set by the app
    entrypoint (e.g. API server) or by scripts/CLIs.
    """

    return logging.getLogger(name)


def make_pgvector_table_name(
    *,
    prefix: str = "chunks",
    embedding_provider: str,
    embedding_model: str,
    embedding_dimensions: int,
) -> str:
    """Generate a safe, stable pgvector table name for a specific embedding config.

    Postgres identifiers are limited to 63 bytes. We keep the name readable and
    add a short hash so different models don't collide.
    """

    provider = re.sub(r"[^a-z0-9_]+", "_", embedding_provider.strip().lower())
    model = embedding_model.strip().lower()
    # Short hash to avoid collisions and keep names short.
    h = hashlib.sha256(model.encode("utf-8", "ignore")).hexdigest()[:8]

    base = f"{prefix}_{provider}_{int(embedding_dimensions)}_{h}"
    # Ensure max identifier length (Postgres: 63 bytes). Our content is ASCII.
    return base[:63]


def make_pgvector_index_name(*, table_name: str, suffix: str) -> str:
    """Generate a safe Postgres index name for a given table.

    Postgres identifiers are limited to 63 bytes. When the table name is already
    at the limit, appending a suffix can overflow and cause DDL failures.

    Strategy:
    - Prefer a readable name: "{table_name}_{suffix}"
    - If too long, truncate and append a stable short hash to avoid collisions.
    """

    base = f"{table_name}_{suffix}"
    if len(base) <= 63:
        return base

    h = hashlib.sha256(base.encode("utf-8", "ignore")).hexdigest()[:8]
    # Leave room for "_" + 8-char hash.
    trimmed = base[: 63 - (1 + len(h))]
    return f"{trimmed}_{h}"

