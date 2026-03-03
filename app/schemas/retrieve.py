from pydantic import BaseModel
from typing import List, Optional


class RetrieveRequest(BaseModel):
    query: str
    chapter: Optional[str] = None
    topK: Optional[int] = 5


class RetrievedChunk(BaseModel):
    text: str
    chapter: Optional[str] = None
    section: Optional[str] = None
    score: Optional[float] = None


class RetrieveResponse(BaseModel):
    chunks: List[RetrievedChunk]


class Error(BaseModel):
    code: Optional[str] = None
    message: Optional[str] = None
