"""Pytest fixtures for ingestion tests — synthetic PDFs generated via PyMuPDF."""

import pytest
import fitz  # PyMuPDF


@pytest.fixture(scope="session")
def sample_pdf_bytes() -> bytes:
    """Synthetic 3-page PDF with title metadata and a 2-level TOC."""
    doc = fitz.open()

    p1 = doc.new_page()
    p1.insert_text(
        (50, 72),
        "Chapter 1: Supply and Demand\n\n"
        "Economics is the study of how people allocate scarce resources among "
        "competing uses. This chapter introduces the foundational concepts of "
        "supply and demand that underpin modern economic theory and practice.",
    )

    p2 = doc.new_page()
    p2.insert_text(
        (50, 72),
        "1.1 What is Economics?\n\n"
        "Economics examines how individuals, businesses, and governments make "
        "decisions when faced with scarcity. Scarcity means that society has "
        "limited resources and therefore cannot produce all the goods and "
        "services people wish to have.",
    )

    p3 = doc.new_page()
    p3.insert_text(
        (50, 72),
        "1.2 Microeconomics and Macroeconomics\n\n"
        "Microeconomics focuses on the decisions of individual consumers and "
        "firms. Macroeconomics examines the economy as a whole, including "
        "topics such as inflation, unemployment, and economic growth.",
    )

    doc.set_toc([
        [1, "Chapter 1: Supply and Demand", 1],
        [2, "1.1 What is Economics?", 2],
        [2, "1.2 Microeconomics and Macroeconomics", 3],
    ])
    doc.set_metadata({"title": "Sample Economics Textbook"})

    data = doc.tobytes()
    doc.close()
    return data


@pytest.fixture(scope="session")
def sample_pdf_multi_chapter_bytes() -> bytes:
    """Synthetic 4-page PDF with two chapters; Chapter 2 has no section on its first page."""
    doc = fitz.open()

    p1 = doc.new_page()
    p1.insert_text(
        (50, 72),
        "Chapter 1: Supply and Demand\n\n"
        "This chapter covers the basics of supply and demand in economics.",
    )

    p2 = doc.new_page()
    p2.insert_text(
        (50, 72),
        "1.1 Introduction to Supply\n\n"
        "Supply refers to the quantity of a good that producers are willing to sell.",
    )

    p3 = doc.new_page()
    p3.insert_text(
        (50, 72),
        "Chapter 2: Markets\n\n"
        "Markets bring together buyers and sellers to exchange goods and services.",
    )

    p4 = doc.new_page()
    p4.insert_text(
        (50, 72),
        "2.1 Market Structures\n\n"
        "Market structures range from perfect competition to monopoly.",
    )

    doc.set_toc([
        [1, "Chapter 1: Supply and Demand", 1],
        [2, "1.1 Introduction to Supply", 2],
        [1, "Chapter 2: Markets", 3],
        [2, "2.1 Market Structures", 4],
    ])
    doc.set_metadata({"title": "Multi-Chapter Textbook"})

    data = doc.tobytes()
    doc.close()
    return data


@pytest.fixture(scope="session")
def sample_pdf_no_toc_bytes() -> bytes:
    """Synthetic 2-page PDF with no TOC bookmarks."""
    doc = fitz.open()

    p1 = doc.new_page()
    p1.insert_text((50, 72), "Introduction\n\nThis document has no table of contents.")

    p2 = doc.new_page()
    p2.insert_text((50, 72), "Conclusion\n\nThis is the second page with no TOC entry.")

    doc.set_metadata({"title": "No TOC Document"})

    data = doc.tobytes()
    doc.close()
    return data
