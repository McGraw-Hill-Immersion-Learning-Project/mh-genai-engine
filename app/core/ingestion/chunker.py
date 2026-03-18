"""Text splitting strategies for chunking documents."""

from dataclasses import dataclass

from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.ingestion.parser import ParsedDocument, TocEntry


@dataclass
class Chunk:
    """A single text chunk with full provenance metadata."""

    text: str
    chunk_id: int       # position in document
    source_key: str     # storage key (e.g. "economics_ch1.pdf")
    title: str          # document-level title from PDF metadata
    page_number: int    # physical page in source document
    chapter: str        # level-1 TOC heading covering this page (empty if no TOC)
    section: str        # level-2 TOC heading covering this page (empty if no TOC)

    def to_metadata(self) -> dict:
        """Return provenance metadata as a dict for vector store storage."""
        return {
            "source_key": self.source_key,
            "title": self.title,
            "page_number": self.page_number,
            "chapter": self.chapter,
            "section": self.section,
            "chunk_id": self.chunk_id,
        }


class TextChunker:
    """Split text into overlapping chunks using recursive character splitting."""

    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
        )

    def chunk(self, doc: ParsedDocument, source_key: str) -> list[Chunk]:
        """Split each page into chunks, preserving page provenance and TOC metadata."""
        chunks: list[Chunk] = []
        chunk_id = 0

        for page in doc.pages:
            if not page.text.strip():
                continue
            chapter, section = self._resolve_toc(page.page_number, doc.toc)

            for piece in self._splitter.split_text(page.text):
                if not piece.strip():
                    continue
                chunks.append(Chunk(
                    text=piece,
                    chunk_id=chunk_id,
                    source_key=source_key,
                    title=doc.title,
                    page_number=page.page_number,
                    chapter=chapter,
                    section=section,
                ))
                chunk_id += 1

        return chunks

    @staticmethod
    def _resolve_toc(page: int, toc: list[TocEntry]) -> tuple[str, str]:
        """Return (chapter, section) for a given page number.

        Iterates TOC entries in order; resets section to "" when a new
        chapter heading is encountered so sections don't bleed across chapters.
        """
        chapter, section = "", ""
        for entry in toc:
            if entry.page <= page:
                if entry.level == 1:
                    chapter = entry.title
                    section = ""
                elif entry.level == 2:
                    section = entry.title
        return chapter, section
