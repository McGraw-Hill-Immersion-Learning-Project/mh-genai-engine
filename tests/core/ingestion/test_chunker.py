"""Chunker unit tests."""

from app.core.ingestion.chunker import TextChunker
from app.core.ingestion.parser import DocumentParser


def test_chunk_count_within_range(sample_pdf_bytes):
    doc = DocumentParser().parse("test.pdf", sample_pdf_bytes)
    chunks = TextChunker().chunk(doc, "test.pdf")
    assert len(chunks) >= 1
    assert len(chunks) <= 30  # 3 pages of modest text should not explode


def test_no_empty_chunks(sample_pdf_bytes):
    doc = DocumentParser().parse("test.pdf", sample_pdf_bytes)
    chunks = TextChunker().chunk(doc, "test.pdf")
    for chunk in chunks:
        assert chunk.text.strip() != ""


def test_all_metadata_fields_present(sample_pdf_bytes):
    doc = DocumentParser().parse("test.pdf", sample_pdf_bytes)
    chunks = TextChunker().chunk(doc, "test.pdf")
    assert chunks, "expected at least one chunk"
    for chunk in chunks:
        assert hasattr(chunk, "source_key")
        assert hasattr(chunk, "title")
        assert hasattr(chunk, "page_number")
        assert hasattr(chunk, "chapter")
        assert hasattr(chunk, "section")
        assert hasattr(chunk, "chunk_id")
        assert hasattr(chunk, "text")


def test_source_key_set_correctly(sample_pdf_bytes):
    doc = DocumentParser().parse("test.pdf", sample_pdf_bytes)
    chunks = TextChunker().chunk(doc, "economics.pdf")
    assert all(c.source_key == "economics.pdf" for c in chunks)


def test_title_set_from_document(sample_pdf_bytes):
    doc = DocumentParser().parse("test.pdf", sample_pdf_bytes)
    chunks = TextChunker().chunk(doc, "test.pdf")
    assert all(c.title == "Sample Economics Textbook" for c in chunks)


def test_page_numbers_valid(sample_pdf_bytes):
    doc = DocumentParser().parse("test.pdf", sample_pdf_bytes)
    chunks = TextChunker().chunk(doc, "test.pdf")
    valid_pages = {p["page_number"] for p in doc.pages}
    for chunk in chunks:
        assert chunk.page_number in valid_pages


def test_chunk_ids_are_sequential(sample_pdf_bytes):
    doc = DocumentParser().parse("test.pdf", sample_pdf_bytes)
    chunks = TextChunker().chunk(doc, "test.pdf")
    assert [c.chunk_id for c in chunks] == list(range(len(chunks)))


def test_chapter_resolved_from_toc(sample_pdf_bytes):
    doc = DocumentParser().parse("test.pdf", sample_pdf_bytes)
    chunks = TextChunker().chunk(doc, "test.pdf")
    # All 3 pages fall under "Chapter 1: Supply and Demand"
    for chunk in chunks:
        assert chunk.chapter == "Chapter 1: Supply and Demand"


def test_section_resolved_from_toc(sample_pdf_bytes):
    doc = DocumentParser().parse("test.pdf", sample_pdf_bytes)
    chunks = TextChunker().chunk(doc, "test.pdf")
    page2_chunks = [c for c in chunks if c.page_number == 2]
    assert page2_chunks, "expected chunks on page 2"
    assert all(c.section == "1.1 What is Economics?" for c in page2_chunks)


def test_no_toc_chapter_and_section_empty(sample_pdf_no_toc_bytes):
    doc = DocumentParser().parse("no_toc.pdf", sample_pdf_no_toc_bytes)
    chunks = TextChunker().chunk(doc, "no_toc.pdf")
    for chunk in chunks:
        assert chunk.chapter == ""
        assert chunk.section == ""
