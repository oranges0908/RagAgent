from typing import Optional

from pydantic import BaseModel


class Paper(BaseModel):
    id: str
    title: str
    filename: str
    uploaded_at: str
    chunk_count: int = 0
    status: str = "processing"


# ── Query 相关 Schema ──────────────────────────────────────────────────────────

class QueryRequest(BaseModel):
    question: str
    paper_id: Optional[str] = None  # None 表示跨全库检索


class Source(BaseModel):
    paper_id: str
    section: str
    chunk_index: int
    text: str        # chunk 原文摘录
    score: float     # L2 距离（越小越相关）


class QueryResponse(BaseModel):
    answer: str
    sources: list[Source]
