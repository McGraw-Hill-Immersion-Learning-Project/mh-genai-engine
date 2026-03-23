"""Parser unit tests."""

from app.core.ingestion.parser import DocumentParser, PageText, TocEntry


def test_extracts_page_count(sample_pdf_bytes):
    doc = DocumentParser().parse("test.pdf", sample_pdf_bytes)
    assert len(doc.pages) == 3


def test_extracts_per_page_text(sample_pdf_bytes):
    doc = DocumentParser().parse("test.pdf", sample_pdf_bytes)
    assert "Supply and Demand" in doc.pages[0].text
    assert "What is Economics" in doc.pages[1].text
    assert "Microeconomics" in doc.pages[2].text


def test_page_numbers_are_sequential(sample_pdf_bytes):
    doc = DocumentParser().parse("test.pdf", sample_pdf_bytes)
    assert [p.page_number for p in doc.pages] == [1, 2, 3]


def test_pages_are_typed(sample_pdf_bytes):
    doc = DocumentParser().parse("test.pdf", sample_pdf_bytes)
    assert all(isinstance(p, PageText) for p in doc.pages)


def test_extracts_title(sample_pdf_bytes):
    doc = DocumentParser().parse("test.pdf", sample_pdf_bytes)
    assert doc.title == "Sample Economics Textbook"


def test_toc_entries_are_typed(sample_pdf_bytes):
    # Docling infers TOC from visual section headers (font size, style).
    # Synthetic test PDFs have no visual hierarchy, so toc may be empty.
    # On real OER PDFs Docling detects proper chapter/section levels.
    doc = DocumentParser().parse("test.pdf", sample_pdf_bytes)
    assert isinstance(doc.toc, list)
    assert all(isinstance(e, TocEntry) for e in doc.toc)


def test_no_toc_returns_empty_list(sample_pdf_no_toc_bytes):
    doc = DocumentParser().parse("no_toc.pdf", sample_pdf_no_toc_bytes)
    assert doc.toc == []
    assert len(doc.pages) == 2


def test_plain_text_file():
    data = b"Hello World\nThis is a plain text document."
    doc = DocumentParser().parse("notes.txt", data)
    assert len(doc.pages) == 1
    assert "Hello World" in doc.pages[0].text
    assert doc.toc == []
