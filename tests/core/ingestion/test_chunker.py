"""Chunker unit tests."""

from app.core.ingestion.chunker import TextChunker
from app.core.ingestion.parser import DocumentParser


def test_chunk_count_within_range(sample_pdf_bytes):
    doc = DocumentParser().parse("test.pdf", sample_pdf_bytes)
    chunks = TextChunker().chunk(doc, "test.pdf")
    assert len(chunks) >= 1
    assert len(chunks) <= 30


def test_no_empty_chunks(sample_pdf_bytes):
    doc = DocumentParser().parse("test.pdf", sample_pdf_bytes)
    chunks = TextChunker().chunk(doc, "test.pdf")
    for chunk in chunks:
        assert chunk.text.strip() != ""


def test_all_metadata_populated(sample_pdf_bytes):
    doc = DocumentParser().parse("test.pdf", sample_pdf_bytes)
    chunks = TextChunker().chunk(doc, "test.pdf")
    assert chunks, "expected at least one chunk"
    for chunk in chunks:
        assert isinstance(chunk.text, str) and chunk.text.strip()
        assert isinstance(chunk.chunk_id, int) and chunk.chunk_id >= 0
        assert isinstance(chunk.source_key, str) and chunk.source_key != ""
        assert isinstance(chunk.title, str) and chunk.title != ""
        assert isinstance(chunk.page_number, int) and chunk.page_number >= 1
        assert isinstance(chunk.chapter, str)
        assert isinstance(chunk.section, str)


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
    valid_pages = {p.page_number for p in doc.pages}
    for chunk in chunks:
        assert chunk.page_number in valid_pages


def test_chunk_ids_are_sequential(sample_pdf_bytes):
    doc = DocumentParser().parse("test.pdf", sample_pdf_bytes)
    chunks = TextChunker().chunk(doc, "test.pdf")
    assert [c.chunk_id for c in chunks] == list(range(len(chunks)))


def test_chapter_resolved_from_toc(sample_pdf_bytes):
    doc = DocumentParser().parse("test.pdf", sample_pdf_bytes)
    chunks = TextChunker().chunk(doc, "test.pdf")
    for chunk in chunks:
        assert chunk.chapter == "Chapter 1: Supply and Demand"


def test_section_page1_empty_before_first_section(sample_pdf_bytes):
    doc = DocumentParser().parse("test.pdf", sample_pdf_bytes)
    chunks = TextChunker().chunk(doc, "test.pdf")
    page1_chunks = [c for c in chunks if c.page_number == 1]
    assert page1_chunks, "expected chunks on page 1"
    assert all(c.section == "" for c in page1_chunks)


def test_section_page2_resolved(sample_pdf_bytes):
    doc = DocumentParser().parse("test.pdf", sample_pdf_bytes)
    chunks = TextChunker().chunk(doc, "test.pdf")
    page2_chunks = [c for c in chunks if c.page_number == 2]
    assert page2_chunks, "expected chunks on page 2"
    assert all(c.section == "1.1 What is Economics?" for c in page2_chunks)


def test_section_page3_resolved(sample_pdf_bytes):
    doc = DocumentParser().parse("test.pdf", sample_pdf_bytes)
    chunks = TextChunker().chunk(doc, "test.pdf")
    page3_chunks = [c for c in chunks if c.page_number == 3]
    assert page3_chunks, "expected chunks on page 3"
    assert all(
        c.section == "1.2 Microeconomics and Macroeconomics"
        for c in page3_chunks
    )


def test_no_toc_chapter_and_section_empty(sample_pdf_no_toc_bytes):
    doc = DocumentParser().parse("no_toc.pdf", sample_pdf_no_toc_bytes)
    chunks = TextChunker().chunk(doc, "no_toc.pdf")
    for chunk in chunks:
        assert chunk.chapter == ""
        assert chunk.section == ""


def test_section_resets_on_new_chapter(sample_pdf_multi_chapter_bytes):
    """Sections from Chapter 1 must not bleed into Chapter 2."""
    doc = DocumentParser().parse("multi.pdf", sample_pdf_multi_chapter_bytes)
    chunks = TextChunker().chunk(doc, "multi.pdf")

    ch2_before_section = [c for c in chunks if c.page_number == 3]
    assert ch2_before_section, "expected chunks on page 3 (Ch2, no section yet)"
    for c in ch2_before_section:
        assert c.chapter == "Chapter 2: Markets"
        assert c.section == "", (
            f"section should be empty before Ch2's first section, got '{c.section}'"
        )

    ch2_with_section = [c for c in chunks if c.page_number == 4]
    assert ch2_with_section, "expected chunks on page 4 (Ch2, Section 2.1)"
    for c in ch2_with_section:
        assert c.chapter == "Chapter 2: Markets"
        assert c.section == "2.1 Market Structures"
