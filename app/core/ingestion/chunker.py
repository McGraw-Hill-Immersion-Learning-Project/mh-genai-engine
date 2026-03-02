"""Text splitting strategies for chunking documents."""

from dataclasses import dataclass

from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.ingestion.parser import ParsedDocument


@dataclass
class Chunk:
    text: str
    index: int        # position in document
    source: str       # storage key (e.g. "economics_ch1.pdf")
    page_number: int  # page in source document


class TextChunker:
    """Split text into overlapping chunks using recursive character splitting."""

    def __init__(self, chunk_size: int = 500, overlap: int = 50):
        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
        )

    def chunk(self, doc: ParsedDocument, source: str) -> list[Chunk]:
        """Split each page into chunks, preserving page number per chunk."""
        chunks = []
        index = 0
        for page in doc.pages:
            if not page["text"].strip():
                continue
            pieces = self._splitter.split_text(page["text"])
            for piece in pieces:
                chunks.append(Chunk(
                    text=piece,
                    index=index,
                    source=source,
                    page_number=page["page_number"],
                ))
                index += 1
        return chunks
