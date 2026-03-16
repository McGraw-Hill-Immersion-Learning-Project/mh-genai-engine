"""Deterministic, cheap dev embedding provider (no external API calls).

Produces fixed-size pseudo-random vectors derived from a hash of the text.
Intended for local/dev runs and tests where semantic quality is not important.
"""

from __future__ import annotations

import hashlib
from typing import List


class DevEmbeddingProvider:
    """Embedding provider that returns deterministic hash-based vectors."""

    def __init__(self, dimensions: int = 8) -> None:
        self._dimensions = dimensions

    def _embed_one(self, text: str) -> list[float]:
        """Compute a deterministic vector for a single text."""
        # Hash the text to 32 bytes
        h = hashlib.sha256(text.encode("utf-8", "ignore")).digest()
        # Use bytes in a rolling fashion to fill the requested dimensions
        vec: List[float] = []
        for i in range(self._dimensions):
            # Take two bytes, interpret as unsigned int
            b1 = h[(2 * i) % len(h)]
            b2 = h[(2 * i + 1) % len(h)]
            val = b1 * 256 + b2  # 0..65535
            # Map to [-1, 1]
            vec.append((val / 32767.5) - 1.0)
        return vec

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Embed a list of texts and return deterministic vectors."""
        if not texts:
            return []
        # This provider is intended for local/dev runs where speed matters more
        # than non-blocking behavior. Avoid per-batch thread hop overhead.
        return [self._embed_one(t) for t in texts]

