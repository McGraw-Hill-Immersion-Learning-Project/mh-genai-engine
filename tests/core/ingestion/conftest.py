"""Pytest fixtures for ingestion tests — synthetic PDFs generated via PyMuPDF."""

import pytest
import fitz  # PyMuPDF

from tests.mocks import FakeEmbeddingProvider, InMemoryVectorStore


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


# ── Service integration test fixtures ─────────────────────────────────────


class FakeStorageProvider:
    """Serves preloaded bytes by key. For testing without filesystem."""

    def __init__(self, files: dict[str, bytes]) -> None:
        self._files = dict(files)

    async def get(self, key: str) -> bytes:
        if key not in self._files:
            raise FileNotFoundError(f"File not found: {key}")
        return self._files[key]

    async def list_files(self, prefix: str = "") -> list[str]:
        return [k for k in self._files if k.startswith(prefix)]

    async def put(self, key: str, data: bytes) -> None:
        self._files[key] = data

    async def delete(self, key: str) -> None:
        if key in self._files:
            del self._files[key]


@pytest.fixture
def fake_embedder() -> FakeEmbeddingProvider:
    """Embedding provider that returns zero vectors (no API calls)."""
    return FakeEmbeddingProvider(dimensions=8)


@pytest.fixture
def in_memory_store() -> InMemoryVectorStore:
    """In-memory vector store for integration tests."""
    return InMemoryVectorStore()


@pytest.fixture
def fake_storage(sample_pdf_bytes: bytes) -> FakeStorageProvider:
    """Storage provider that serves the sample PDF."""
    return FakeStorageProvider({"sample.pdf": sample_pdf_bytes})
