"""
QueryService 单元测试

使用 mock LLMProvider，避免真实 API 调用。
运行：pytest tests/test_query_service.py -v
"""
import sqlite3
import uuid
from pathlib import Path
from typing import Optional
from unittest.mock import AsyncMock, MagicMock

import numpy as np
import pytest
import pytest_asyncio

from backend.core.faiss_store import FAISSStore, SearchResult
from backend.core.llm_provider import LLMProvider
from backend.db.models import QueryResponse
from backend.services.query_service import QueryService


# ── Mock 依赖 ──────────────────────────────────────────────────────────────────

class MockEmbedder:
    """固定返回随机向量（维度 384）"""
    dim = 384

    def embed(self, texts: list[str]) -> np.ndarray:
        rng = np.random.default_rng(seed=42)
        return rng.random((len(texts), self.dim)).astype(np.float32)


class MockLLMProvider(LLMProvider):
    """固定返回预设答案，记录调用次数"""

    def __init__(self):
        self.call_count = 0
        self.last_prompt: Optional[str] = None

    async def complete(self, prompt: str) -> str:
        self.call_count += 1
        self.last_prompt = prompt
        return "This is a mocked answer."


# ── Fixtures ───────────────────────────────────────────────────────────────────

FIXED_PAPER_ID = "aaaaaaaa-0000-0000-0000-000000000001"


@pytest.fixture()
def tmp_db(tmp_path):
    """在临时目录创建一个包含一条 ready paper 的 SQLite DB（使用固定 paper_id）"""
    db_file = tmp_path / "papers.db"
    conn = sqlite3.connect(str(db_file))
    conn.execute("""
        CREATE TABLE papers (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            filename TEXT NOT NULL,
            uploaded_at TEXT NOT NULL,
            chunk_count INTEGER NOT NULL DEFAULT 0,
            status TEXT NOT NULL DEFAULT 'processing'
        )
    """)
    conn.execute(
        "INSERT INTO papers VALUES (?, ?, ?, ?, ?, ?)",
        (FIXED_PAPER_ID, "Test Paper", "test.pdf", "2026-01-01T00:00:00Z", 3, "ready"),
    )
    conn.commit()
    conn.close()
    return db_file


@pytest_asyncio.fixture()
async def aio_db(tmp_db):
    import aiosqlite
    async with aiosqlite.connect(str(tmp_db)) as db:
        yield db


@pytest.fixture()
def store_with_data(monkeypatch, tmp_path):
    """FAISSStore with 3 pre-loaded chunks，使用与 aio_db 相同的固定 paper_id"""
    monkeypatch.setattr("backend.core.faiss_store.FAISS_DIR", tmp_path)

    store = FAISSStore()
    dim = MockEmbedder.dim
    rng = np.random.default_rng(seed=0)
    vectors = rng.random((3, dim)).astype(np.float32)
    metadata = [
        {"chunk_index": i, "section": "Abstract", "text": f"chunk text {i}",
         "char_start": 0, "char_end": 10}
        for i in range(3)
    ]
    store.add(FIXED_PAPER_ID, vectors, metadata)
    store.save(FIXED_PAPER_ID)
    return store


# ── Tests ──────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_query_returns_response(aio_db, store_with_data):
    llm = MockLLMProvider()
    svc = QueryService(store_with_data, MockEmbedder(), llm, aio_db)
    response = await svc.query("What is the method?", paper_id=FIXED_PAPER_ID)

    assert isinstance(response, QueryResponse)
    assert response.answer == "This is a mocked answer."
    assert len(response.sources) > 0


@pytest.mark.asyncio
async def test_query_calls_llm_once(aio_db, store_with_data):
    llm = MockLLMProvider()
    svc = QueryService(store_with_data, MockEmbedder(), llm, aio_db)
    await svc.query("What is the method?", paper_id=FIXED_PAPER_ID)

    assert llm.call_count == 1


@pytest.mark.asyncio
async def test_query_prompt_contains_question(aio_db, store_with_data):
    llm = MockLLMProvider()
    svc = QueryService(store_with_data, MockEmbedder(), llm, aio_db)
    question = "What is the main contribution?"
    await svc.query(question, paper_id=FIXED_PAPER_ID)

    assert question in llm.last_prompt


@pytest.mark.asyncio
async def test_query_empty_question_raises(aio_db, store_with_data):
    svc = QueryService(store_with_data, MockEmbedder(), MockLLMProvider(), aio_db)
    with pytest.raises(ValueError, match="empty"):
        await svc.query("   ")


@pytest.mark.asyncio
async def test_query_invalid_paper_id_raises(aio_db, store_with_data):
    svc = QueryService(store_with_data, MockEmbedder(), MockLLMProvider(), aio_db)
    with pytest.raises(KeyError):
        await svc.query("What is X?", paper_id="nonexistent-id")


@pytest.mark.asyncio
async def test_sources_fields(aio_db, store_with_data):
    svc = QueryService(store_with_data, MockEmbedder(), MockLLMProvider(), aio_db)
    response = await svc.query("What is X?", paper_id=FIXED_PAPER_ID)

    for src in response.sources:
        assert src.paper_id == FIXED_PAPER_ID
        assert isinstance(src.chunk_index, int)
        assert isinstance(src.score, float)
        assert isinstance(src.text, str)
