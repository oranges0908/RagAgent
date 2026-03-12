from typing import Optional

from pydantic import BaseModel


class Paper(BaseModel):
    id: str
    title: str
    filename: str
    uploaded_at: str
    chunk_count: int = 0
    status: str = "processing"
    file_hash: Optional[str] = None


# ── Query 相关 Schema ──────────────────────────────────────────────────────────

class QueryRequest(BaseModel):
    question: str
    paper_id: Optional[str] = None  # None 表示跨全库检索


class Source(BaseModel):
    paper_id: str
    section: str
    chunk_index: int
    text: str               # 命中 chunk 原文（LLM prompt 用）
    score: float            # L2 距离（越小越相关）
    context_text: str = ""  # 扩展上下文（±2 相邻 chunk，前端展示用）


class QueryResponse(BaseModel):
    answer: str
    sources: list[Source]
