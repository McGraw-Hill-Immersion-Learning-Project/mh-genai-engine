import os
import pymupdf
import re
import uuid
from datetime import datetime

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_chroma import Chroma
from langchain_huggingface.embeddings import HuggingFaceEmbeddings
from langchain_community.llms import Ollama
from langchain_classic.chains import RetrievalQA
from langchain_core.prompts import PromptTemplate


# -------------------------------
# CONFIG
# -------------------------------

PDF_PATH = "Economics3e-WEB_AObkTqf.pdf"
DOC_ID = "economics3e"

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 150
PERSIST_DIRECTORY = "./economics3e_index"

OLLAMA_MODEL = "llama3:8b"


# -------------------------------
# EXTRACTION
# -------------------------------

def extract_text_from_pdf(path):
    doc = pymupdf.open(path)
    full_text = ""

    for page_num, page in enumerate(doc):
        text = page.get_text("text")
        full_text += f"\n\n--- Page {page_num + 1} ---\n"
        full_text += text

    doc.close()
    return full_text


def normalize_text(text):
    text = re.sub(r"--- Page \d+ ---", "", text)
    text = re.sub(r"-\n", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def split_by_subsection(text):
    pattern = r"\n(?=\d+\.\d+\s+[A-Z])"
    sections = re.split(pattern, text)
    return [s.strip() for s in sections if re.match(r"^\d+\.\d+\s+", s)]


# -------------------------------
# SPLITTER
# -------------------------------

def get_splitter():
    return RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP
    )


def build_documents(subsection_text):
    splitter = get_splitter()

    header_line = subsection_text.split("\n")[0].strip()
    subsection_number = header_line.split()[0]
    subsection_title = header_line[len(subsection_number):].strip()
    chapter_number = subsection_number.split(".")[0]

    body = subsection_text[len(header_line):].strip()
    chunks = splitter.split_text(body)

    documents = []

    for idx, chunk in enumerate(chunks):
        if len(chunk.strip()) < 200:
            continue

        metadata = {
            "id": str(uuid.uuid4()),
            "doc_id": DOC_ID,
            "chapter": int(chapter_number),
            "subsection": subsection_number,
            "title": subsection_title
        }

        documents.append(
            Document(
                page_content=chunk,
                metadata=metadata
            )
        )

    return documents


# -------------------------------
# VECTOR STORE
# -------------------------------

def get_embeddings():
    return HuggingFaceEmbeddings(
        model_name="BAAI/bge-large-en-v1.5",
        model_kwargs={"device": "cpu"},  # change to "cuda" if GPU available
        encode_kwargs={"normalize_embeddings": True}
    )


def build_vectorstore(documents):
    embeddings = get_embeddings()

    vectorstore = Chroma.from_documents(
        documents=documents,
        embedding=embeddings,
        persist_directory=PERSIST_DIRECTORY
    )

    return vectorstore


def load_vectorstore():
    embeddings = get_embeddings()

    return Chroma(
        persist_directory=PERSIST_DIRECTORY,
        embedding_function=embeddings
    )


# -------------------------------
# OLLAMA + RETRIEVAL QA
# -------------------------------

def build_qa_chain(vectorstore):

    retriever = vectorstore.as_retriever(search_kwargs={"k": 4})

    prompt_template = """
You are answering strictly using the provided textbook context.
If the answer is not in the context, say:
"I cannot find this in the provided material."

Context:
{context}

Question:
{question}

Answer:
"""

    prompt = PromptTemplate(
        template=prompt_template,
        input_variables=["context", "question"]
    )

    llm = Ollama(
        model=OLLAMA_MODEL,
        temperature=0.0
    )

    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        retriever=retriever,
        return_source_documents=True,
        chain_type_kwargs={"prompt": prompt}
    )

    return qa_chain


# -------------------------------
# MAIN
# -------------------------------

if __name__ == "__main__":

    # ---- First-time ingestion only if index does not exist ----
    if not os.path.exists(PERSIST_DIRECTORY):

        print("Building vector index...")

        raw_text = extract_text_from_pdf(PDF_PATH)
        normalized_text = normalize_text(raw_text)
        subsections = split_by_subsection(normalized_text)

        all_documents = []
        for subsection in subsections:
            docs = build_documents(subsection)
            all_documents.extend(docs)

        print("Total documents:", len(all_documents))

        vectorstore = build_vectorstore(all_documents)

    else:
        print("Loading existing vector index...")
        vectorstore = load_vectorstore()

    # ---- Build QA Chain ----
    qa_chain = build_qa_chain(vectorstore)

    # ---- Interactive Loop ----
    while True:
        query = input("\nAsk a question (or type 'exit'): ")

        if query.lower() == "exit":
            break

        response = qa_chain(query)

        print("\nANSWER:\n")
        print(response["result"])

        print("\nSOURCES:\n")
        for doc in response["source_documents"]:
            print(f"Chapter {doc.metadata['chapter']}, ",
            f"Section {doc.metadata['subsection']}, ",
            f"Chunk {doc.metadata['title']}")