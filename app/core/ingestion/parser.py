"""Extract text from PDF, txt, and other document formats."""

from dataclasses import dataclass, field

import fitz  # PyMuPDF


@dataclass
class ParsedDocument:
    """Output of parsing a document — per-page text plus PDF-level metadata."""
    pages: list[dict]        # [{"page_number": int, "text": str}]
    title: str = ""
    toc: list = field(default_factory=list)  # [[level, title, page], ...]


class DocumentParser:
    """Parse raw document bytes into structured per-page text."""

    def parse(self, key: str, data: bytes) -> ParsedDocument:
        """Parse document bytes. Routes by file extension."""
        if key.lower().endswith(".pdf"):
            return self._parse_pdf(data)
        text = data.decode("utf-8", errors="replace")
        return ParsedDocument(pages=[{"page_number": 1, "text": text}])

    def _parse_pdf(self, data: bytes) -> ParsedDocument:
        """Extract per-page text, title, and TOC from PDF bytes using PyMuPDF.

        TOC is best-effort — returns empty list if the PDF has none.
        """
        doc = fitz.open(stream=data, filetype="pdf")
        title = doc.metadata.get("title", "")
        toc = doc.get_toc()  # [[level, title, page_number], ...] or []
        pages = [
            {"page_number": i + 1, "text": page.get_text()}
            for i, page in enumerate(doc)
        ]
        doc.close()
        return ParsedDocument(pages=pages, title=title, toc=toc)
