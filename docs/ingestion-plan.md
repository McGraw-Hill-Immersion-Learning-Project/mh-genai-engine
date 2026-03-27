# OER Selection and Ingestion Plan

## 1. OER Selected

**Textbook:** Principles of Economics (OpenStax)

**File:** `data/raw/Economics_OER.pdf`
**File Origin** https://openstax.org/details/books/principles-economics-3e

**Source:** OpenStax (openstax.org) -- openly licensed under CC BY 4.0, free to use and redistribute.

**Why this OER:**

- Widely adopted in introductory economics courses, making it relevant to McGraw-Hill's target audience.
- Available as a well-structured PDF with a machine-readable table of contents, which enables automatic chapter and section tagging.
- CC BY 4.0 license allows use in a commercial POC without legal concerns.
- Broad subject coverage (micro and macro) provides enough content diversity to stress-test retrieval quality.

## 2. Sample Chapter

**Chapter extracted:** Chapter 1 -- Welcome to Economics

The full PDF is used for ingestion in Sprint 1. A single-chapter extract can be produced from the PDF using PyMuPDF (still available as a dev dependency) if needed for isolated testing.

## 3. Chunking Strategy

Chunking uses `RecursiveCharacterTextSplitter` from `langchain-text-splitters`.

| Parameter  | Value                         | Rationale                                                                                                       |
| ---------- | ----------------------------- | --------------------------------------------------------------------------------------------------------------- |
| Chunk size | 500 characters                | Fits comfortably within embedding model input limits (BGE base: 512 tokens). Keeps chunks semantically focused. |
| Overlap    | 50 characters                 | Preserves context across chunk boundaries so retrieval does not miss cross-boundary sentences.                  |
| Separators | `\n\n`, `\n`, `. `, ` `, `""` | Tries to split on paragraph, then sentence, then word boundaries before hard-splitting.                         |

**Per-page chunking:** Text is extracted page by page via Docling. Each page is chunked independently and every chunk is tagged with its source page number (from Docling's `prov[0].page_no`), preserving page provenance for citations.

**Known limitation:** Paragraphs spanning a page break are split at the boundary, which can produce incomplete chunks. The 50-character overlap partially mitigates this.

**Planned upgrade (global-text chunking):** Replace per-page chunking with global-text chunking: extract all page text as one continuous string while building a character-offset-to-page map, chunk the full text so `RecursiveCharacterTextSplitter` finds natural paragraph/sentence boundaries, then assign `page_number` per chunk via the offset map. This preserves citation accuracy without sacrificing chunk quality.

**Planned experiments:** The current character-based strategy is a starting point. We plan to evaluate the following alternatives in later sprints:

- **Structural chunking:** Split on document structure (chapters, sections, subsections) using the PDF TOC rather than character count. Keeps semantically complete units together and improves citation granularity.
- **Semantic chunking:** Group sentences by embedding similarity so chunk boundaries fall at topic shifts rather than fixed character limits.
- **Sentence-window chunking:** Store individual sentences but retrieve surrounding context windows, balancing precision and context for the LLM.

The baseline (recursive character split) will be compared against these strategies using the golden prompt test set.

## 4. Metadata Plan

Each chunk stored in pgvector carries the following metadata:

| Field         | Source                          | Purpose                                                      |
| ------------- | ------------------------------- | ------------------------------------------------------------ |
| `source_key`  | Storage key (filename)          | Identifies the document file for citation.                   |
| `title`       | Embedded PDF document metadata  | Document-level title for display.                            |
| `page_number` | Physical page number in the PDF | Page-level provenance for citations.                         |
| `chapter`     | PDF table of contents (level 1) | Section provenance; resolved by matching page number to TOC. |
| `section`     | PDF table of contents (level 2) | Sub-section provenance; used in citations.                   |
| `chunk_id`    | Chunk position in document      | Internal ordering for debug and tracing.                     |

**TOC resolution:** `chapter` and `section` are derived at ingest time using the PDF's table of contents. For each chunk, its physical page number is used to look up the most recent chapter and section heading that started on or before that page. If the PDF has no TOC, both fields are left empty.

**Query-time RAG (downstream):** Lesson-outline generation applies **metadata filters** on the vector store using `chapter` (exact), `section` (exact), `sub_section` (prefix match on stored `section` label), and `book` (case-insensitive substring on `title`). Catalog / Dashboard values for `LessonOutlineRequest` should align with how TOC text is stored in `metadata` (mismatches yield zero retrieved chunks). Semantic retrieval uses a separate embed string built from the learning objective and pedagogy hints, not from chapter labels alone. The Engine returns **one API citation per retrieved chunk** (stable index for UI grounding); each **`snippet`** is a short preview — full passage quality depends on extraction (future: layout-aware parsers such as Docling).

## 5. Ingestion Pipeline Overview

```
PDF / TXT file (storage)
        |
   Document Parser       -- Docling (standard pipeline); extracts per-page Markdown text, title (via pypdfium2 metadata), TOC (from visual section headers)
        |
   Text Chunker          -- RecursiveCharacterTextSplitter (500 chars, 50 overlap)
        |
   Embedding Provider    -- batched (default batch size 64) to minimize API round-trips
        |
   Vector Store          -- pgvector (PostgreSQL + vector extension), HNSW cosine index
```

**Vector store:** pgvector is the sole vector store. Local dev uses Docker: `docker compose up db` starts Postgres with pgvector. See `docs/runbook.md` for setup.

## 6. Test Strategy

**Test fixture:** A small synthetic PDF (2-3 pages, known text content, with a TOC/bookmarks) committed to `tests/fixtures/`. Known content allows deterministic assertions.

**Parser unit tests** (`tests/core/ingestion/test_parser.py`):

- Extracts correct text from each page.
- Returns correct page count.
- Extracts TOC entries (chapter/section titles and page numbers).
- Handles a PDF with no TOC gracefully (empty list, no crash).

**Chunker unit tests** (`tests/core/ingestion/test_chunker.py`):

- Chunk count is within expected range for known input.
- No empty chunks produced.
- Every chunk has all required metadata fields (`source_key`, `title`, `page_number`, `chapter`, `section`, `chunk_id`).
- `page_number` values are valid (within document page range).

**Service integration test** (`tests/core/ingestion/test_service.py`):

- Uses a mock embedding provider (returns fixed-dimension zero vectors) to avoid API calls.
- Uses a mock vector store (in-memory list) to avoid DB dependency.
- Verifies full pipeline: PDF in → chunks with embeddings stored.
