"""Chunker unit tests."""

from app.core.ingestion.chunker import TextChunker
from app.core.ingestion.parser import DocumentParser, PageText, ParsedDocument, TocEntry


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


def _doc_with_toc() -> ParsedDocument:
    """Minimal ParsedDocument with a 2-level TOC for chunker resolution tests.

    Constructed directly so these tests are independent of the parser and
    Docling's visual heading-level inference.
    """
    return ParsedDocument(
        pages=[
            PageText(page_number=1, text="Chapter 1: Supply and Demand\n\nEconomics is the study of scarce resource allocation."),
            PageText(page_number=2, text="1.1 What is Economics?\n\nEconomics examines individual and government decision-making."),
            PageText(page_number=3, text="1.2 Microeconomics and Macroeconomics\n\nMicro focuses on individuals; macro on the whole economy."),
        ],
        title="Sample Economics Textbook",
        toc=[
            TocEntry(level=1, title="Chapter 1: Supply and Demand", page=1),
            TocEntry(level=2, title="1.1 What is Economics?", page=2),
            TocEntry(level=2, title="1.2 Microeconomics and Macroeconomics", page=3),
        ],
    )


def test_chapter_resolved_from_toc():
    chunks = TextChunker().chunk(_doc_with_toc(), "test.pdf")
    for chunk in chunks:
        assert chunk.chapter == "Chapter 1: Supply and Demand"


def test_section_page1_empty_before_first_section():
    chunks = TextChunker().chunk(_doc_with_toc(), "test.pdf")
    page1_chunks = [c for c in chunks if c.page_number == 1]
    assert page1_chunks, "expected chunks on page 1"
    assert all(c.section == "" for c in page1_chunks)


def test_section_page2_resolved():
    chunks = TextChunker().chunk(_doc_with_toc(), "test.pdf")
    page2_chunks = [c for c in chunks if c.page_number == 2]
    assert page2_chunks, "expected chunks on page 2"
    assert all(c.section == "1.1 What is Economics?" for c in page2_chunks)


def test_section_page3_resolved():
    chunks = TextChunker().chunk(_doc_with_toc(), "test.pdf")
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


def test_section_resets_on_new_chapter():
    """Sections from Chapter 1 must not bleed into Chapter 2."""
    doc = ParsedDocument(
        pages=[
            PageText(page_number=1, text="Chapter 1: Supply and Demand\n\nBasics of supply and demand."),
            PageText(page_number=2, text="1.1 Introduction to Supply\n\nSupply is the quantity producers will sell."),
            PageText(page_number=3, text="Chapter 2: Markets\n\nMarkets bring buyers and sellers together."),
            PageText(page_number=4, text="2.1 Market Structures\n\nStructures range from competition to monopoly."),
        ],
        title="Multi-Chapter Textbook",
        toc=[
            TocEntry(level=1, title="Chapter 1: Supply and Demand", page=1),
            TocEntry(level=2, title="1.1 Introduction to Supply", page=2),
            TocEntry(level=1, title="Chapter 2: Markets", page=3),
            TocEntry(level=2, title="2.1 Market Structures", page=4),
        ],
    )
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
