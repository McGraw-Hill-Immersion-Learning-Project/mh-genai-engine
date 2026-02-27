"""Text splitting strategies for chunking documents."""

from dataclasses import dataclass

from langchain_text_splitters import RecursiveCharacterTextSplitter


@dataclass
class Chunk:
    text: str
    index: int   # position in document
    source: str  # storage key (e.g. "biology_ch1.pdf")


class TextChunker:
    """Split text into overlapping chunks using recursive character splitting."""

    def __init__(self, chunk_size: int = 500, overlap: int = 50):
        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
        )

    def chunk(self, text: str, source: str) -> list[Chunk]:
        """Split text into chunks with overlap, preserving natural boundaries."""
        pieces = self._splitter.split_text(text)
        return [Chunk(text=piece, index=i, source=source) for i, piece in enumerate(pieces)]