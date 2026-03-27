"""Extract text from PDF, txt, and other document formats."""

import os
import tempfile
from collections import defaultdict
from dataclasses import dataclass, field

import pypdfium2 as pdfium  # used only to read embedded PDF title metadata; Docling does not surface it
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import ThreadedPdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling_core.types.doc import DocItemLabel, SectionHeaderItem, TableItem, TextItem

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

    def __init__(
        self,
        *,
        do_ocr: bool = True,
        do_table_structure: bool = True,
        ocr_batch_size: int = 4,
        layout_batch_size: int = 4,
        table_batch_size: int = 4,
        queue_max_size: int = 16,
    ) -> None:
        pdf_pipeline = ThreadedPdfPipelineOptions(
            do_ocr=do_ocr,
            do_table_structure=do_table_structure,
            ocr_batch_size=ocr_batch_size,
            layout_batch_size=layout_batch_size,
            table_batch_size=table_batch_size,
            queue_max_size=queue_max_size,
        )
        self._converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(
                    pipeline_options=pdf_pipeline,
                ),
            },
        )

    def parse(self, key: str, data: bytes) -> ParsedDocument:
        """Parse document bytes. Routes by file extension."""
        if key.lower().endswith(".pdf"):
            return self._parse_pdf(data)
        text = data.decode("utf-8", errors="replace")
        return ParsedDocument(pages=[PageText(page_number=1, text=text)])

    def _parse_pdf(self, data: bytes) -> ParsedDocument:
        """Convert PDF bytes to per-page Markdown text using Docling.

        Docling performs layout analysis to produce structured Markdown
        (headings, tables, lists) rather than raw flat text. Page provenance
        is preserved via each item's prov[0].page_no field.

        TOC strategy: use embedded PDF bookmarks when present (more accurate,
        author-intended structure), otherwise fall back to Docling's visual
        SECTION_HEADER detection (handles OER PDFs that lack bookmarks).
        """
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(data)
            tmp_path = tmp.name

        try:
            result = self._converter.convert(tmp_path)
        finally:
            os.unlink(tmp_path)

        # Read title and embedded bookmarks via pypdfium2 — Docling does not surface these.
        pdf_doc = pdfium.PdfDocument(data)
        title = pdf_doc.get_metadata_dict().get("Title", "")
        bookmark_toc = self._extract_bookmark_toc(pdf_doc)
        pdf_doc.close()

        doc = result.document

        pages_content: dict[int, list[str]] = defaultdict(list)
        # use Docling heading inference only when the PDF has no embedded bookmarks
        docling_toc: list[TocEntry] = []

        for item, _ in doc.iterate_items():
            # skip items with no page provenance (e.g. document-level metadata)
            if not item.prov:
                continue
            page_no = item.prov[0].page_no

            if item.label == DocItemLabel.TITLE:
                # document title — render as top-level heading on its page
                pages_content[page_no].append(f"# {item.text}")

            elif item.label == DocItemLabel.SECTION_HEADER and isinstance(item, SectionHeaderItem):
                # section heading — render with correct Markdown depth
                heading_prefix = "#" * item.level
                pages_content[page_no].append(f"{heading_prefix} {item.text}")
                if item.level <= 2:  # only chapter (1) and section (2) headings go in the TOC
                    docling_toc.append(TocEntry(level=item.level, title=item.text, page=page_no))

            elif item.label == DocItemLabel.TABLE and isinstance(item, TableItem):
                # export tables as Markdown so the chunker sees structured rows
                pages_content[page_no].append(item.export_to_markdown(doc))

            elif isinstance(item, TextItem) and item.text.strip():
                # plain paragraph text
                pages_content[page_no].append(item.text)

        # prefer embedded bookmarks; fall back to Docling's visual heading inference
        toc = bookmark_toc if bookmark_toc else docling_toc

        # assemble per-page objects, sorted by page number, skipping blank pages
        pages = [
            PageText(page_number=pg, text="\n\n".join(parts))
            for pg, parts in sorted(pages_content.items())
            if any(p.strip() for p in parts)
        ]

        return ParsedDocument(pages=pages, title=title, toc=toc)

    def _extract_bookmark_toc(self, pdf_doc: pdfium.PdfDocument) -> list[TocEntry]:
        """Extract TOC from embedded PDF bookmarks (levels 1–2 only).

        Returns an empty list if the PDF has no bookmarks, which signals the
        caller to fall back to Docling's visual heading detection.
        """
        toc: list[TocEntry] = []
        for bookmark in pdf_doc.get_toc():
            if bookmark.level > 1:  # 0-based: keep level 0 (chapter) and 1 (section)
                continue
            dest = bookmark.get_dest()
            if dest is None:
                continue
            page_index = dest.get_index()
            if page_index is None:
                continue
            toc.append(TocEntry(
                level=bookmark.level + 1,  # convert 0-based to 1-based to match TocEntry convention
                title=bookmark.get_title(),
                page=page_index + 1,       # convert 0-based page index to 1-indexed page number
            ))
        return toc
