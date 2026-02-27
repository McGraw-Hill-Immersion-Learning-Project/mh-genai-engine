"""BGE embedding provider using BAAI/bge-base-en-v1.5 (local, no API key required)."""

import asyncio
from functools import partial

from sentence_transformers import SentenceTransformer


class BGEEmbeddingProvider:
    """Embed texts locally using BAAI/bge-base-en-v1.5.

    BGE models expect a query prefix at retrieval time for best results:
      - ingestion (documents): no prefix
      - retrieval (queries): prefix "Represent this sentence for searching relevant passages: "
    """

    MODEL = "BAAI/bge-base-en-v1.5"
    QUERY_PREFIX = "Represent this sentence for searching relevant passages: "

    def __init__(self):
        self._model = SentenceTransformer(self.MODEL)

    async def embed(self, texts: list[str], input_type: str = "document") -> list[list[float]]:
        """Embed a list of texts. input_type='document' for ingestion, 'query' for retrieval."""
        if input_type == "query":
            texts = [self.QUERY_PREFIX + t for t in texts]

        loop = asyncio.get_event_loop()
        encode = partial(self._model.encode, texts, normalize_embeddings=True)
        vectors = await loop.run_in_executor(None, encode)
        return vectors.tolist()
