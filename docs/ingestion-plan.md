# OER Selection and Ingestion Plan

## 1. OER Selected

**Textbook:** Principles of Economics (OpenStax)
**File:** `data/raw/Economics_OER.pdf`
**Source:** OpenStax (openstax.org) -- openly licensed under CC BY 4.0, free to use and redistribute.

**Why this OER:**

- Widely adopted in introductory economics courses, making it relevant to McGraw-Hill's target audience.
- Available as a well-structured PDF with a machine-readable table of contents, which enables automatic chapter and section tagging.
- CC BY 4.0 license allows use in a commercial POC without legal concerns.
- Broad subject coverage (micro and macro) provides enough content diversity to stress-test retrieval quality.

## 2. Sample Chapter

**Chapter extracted:** Chapter 1 -- Welcome to Economics

The full PDF is used for ingestion in Sprint 1. A single-chapter extract can be produced from the PDF using PyMuPDF if needed for isolated testing.

## 3. Chunking Strategy

Chunking uses `RecursiveCharacterTextSplitter` from `langchain-text-splitters`.

| Parameter  | Value                         | Rationale                                                                                                       |
| ---------- | ----------------------------- | --------------------------------------------------------------------------------------------------------------- |
| Chunk size | 500 characters                | Fits comfortably within embedding model input limits (BGE base: 512 tokens). Keeps chunks semantically focused. |
| Overlap    | 50 characters                 | Preserves context across chunk boundaries so retrieval does not miss cross-boundary sentences.                  |
| Separators | `\n\n`, `\n`, `. `, ` `, `""` | Tries to split on paragraph, then sentence, then word boundaries before hard-splitting.                         |

**Per-page chunking:** Text is extracted page by page via PyMuPDF. Each page is chunked independently and every chunk is tagged with its source page number, preserving page provenance for citations.

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

## 5. Ingestion Pipeline Overview

```
PDF / TXT file (storage)
        |
   Document Parser       -- PyMuPDF; extracts per-page text, title, TOC
        |
   Text Chunker          -- RecursiveCharacterTextSplitter (500 chars, 50 overlap)
        |
   Embedding Provider    -- BAAI/bge-base-en-v1.5 (local, 768-dim, normalized)
        |
   Vector Store          -- PostgreSQL + pgvector, HNSW cosine index
```
