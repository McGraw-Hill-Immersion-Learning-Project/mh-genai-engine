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


def test_extracts_toc_entries(sample_pdf_bytes):
    doc = DocumentParser().parse("test.pdf", sample_pdf_bytes)
    assert len(doc.toc) == 3
    assert all(isinstance(e, TocEntry) for e in doc.toc)
    levels = [e.level for e in doc.toc]
    headings = [e.title for e in doc.toc]
    assert levels == [1, 2, 2]
    assert "Chapter 1: Supply and Demand" in headings
    assert "1.1 What is Economics?" in headings


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
