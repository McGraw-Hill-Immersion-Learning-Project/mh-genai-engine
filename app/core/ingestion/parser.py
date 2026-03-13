"""Extract text from PDF, txt, and other document formats."""

from dataclasses import dataclass, field

import fitz  # PyMuPDF


@dataclass
class PageText:
    """Text content of a single page."""

    page_number: int  # 1-indexed physical page
    text: str


@dataclass
class TocEntry:
    """Single entry from the PDF table of contents."""

    level: int   # 1 = chapter, 2 = section
    title: str
    page: int    # 1-indexed page where this heading starts


@dataclass
class ParsedDocument:
    """Output of parsing a document — per-page text plus PDF-level metadata."""

    pages: list[PageText]
    title: str = ""
    toc: list[TocEntry] = field(default_factory=list)


class DocumentParser:
    """Parse raw document bytes into structured per-page text."""

    def parse(self, key: str, data: bytes) -> ParsedDocument:
        """Parse document bytes. Routes by file extension."""
        if key.lower().endswith(".pdf"):
            return self._parse_pdf(data)
        text = data.decode("utf-8", errors="replace")
        return ParsedDocument(pages=[PageText(page_number=1, text=text)])

    def _parse_pdf(self, data: bytes) -> ParsedDocument:
        """Extract per-page text, title, and TOC from PDF bytes using PyMuPDF.

        TOC is best-effort — returns empty list if the PDF has none.
        """
        with fitz.open(stream=data, filetype="pdf") as doc:
            title = doc.metadata.get("title", "")
            toc = [
                TocEntry(level=lvl, title=heading, page=pg)
                for lvl, heading, pg in doc.get_toc()
            ]
            pages = [
                PageText(page_number=i + 1, text=page.get_text())
                for i, page in enumerate(doc)
            ]
        return ParsedDocument(pages=pages, title=title, toc=toc)
