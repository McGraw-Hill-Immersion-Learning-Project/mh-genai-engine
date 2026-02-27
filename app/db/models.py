"""Collection schemas and document metadata types for the vector store."""
from pydantic import BaseModel

class DocumentChunk(BaseModel):
    """A chunk of text extracted from a document."""
    id: str 
    text: str
    source_key: str = "" # filename e.g. "biology_ch1.pdf"
    book_id: str = "" # unique book identifier 
    title: str = "" # book title 
    subject: str = "" # book subject e.g. "biology" "economics"
    chapter: str = "" # chapter title e.g. "chapter 1: cell structure"
    section: str = "" # e.g. 1.2 - used in citations 
    page_number: int = 0 # page number in the source document 
    chunk_id: int = 0  #position in source doc (internal)
    score: float = 0.0 # similarity score from vector search 