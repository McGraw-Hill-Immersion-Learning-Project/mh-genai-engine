"""Text splitting strategies for chunking documents."""

from dataclasses import dataclass

from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.ingestion.parser import ParsedDocument


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


class TextChunker:
    """Split text into overlapping chunks using recursive character splitting."""

    def __init__(self, chunk_size: int = 500, overlap: int = 50):
        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
        )

    def chunk(self, doc: ParsedDocument, source_key: str) -> list[Chunk]:
        """Split each page into chunks, preserving page provenance and TOC metadata."""
        chapter_map, section_map = self._build_toc_maps(doc.toc)
        chunks: list[Chunk] = []
        chunk_id = 0

        for page in doc.pages:
            if not page["text"].strip():
                continue
            page_num = page["page_number"]
            chapter = self._resolve(chapter_map, page_num)
            section = self._resolve(section_map, page_num)

            for piece in self._splitter.split_text(page["text"]):
                if not piece.strip():
                    continue
                chunks.append(Chunk(
                    text=piece,
                    chunk_id=chunk_id,
                    source_key=source_key,
                    title=doc.title,
                    page_number=page_num,
                    chapter=chapter,
                    section=section,
                ))
                chunk_id += 1

        return chunks

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _build_toc_maps(toc: list) -> tuple[dict[int, str], dict[int, str]]:
        """Build page→heading maps for level-1 (chapter) and level-2 (section)."""
        chapter_map: dict[int, str] = {}
        section_map: dict[int, str] = {}
        for level, heading, page in toc:
            if level == 1:
                chapter_map[page] = heading
            elif level == 2:
                section_map[page] = heading
        return chapter_map, section_map

    @staticmethod
    def _resolve(mapping: dict[int, str], page_num: int) -> str:
        """Return the most recent heading that started on or before page_num."""
        candidates = [p for p in mapping if p <= page_num]
        if not candidates:
            return ""
        return mapping[max(candidates)]
