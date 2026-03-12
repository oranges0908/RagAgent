import json
from typing import AsyncIterator

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from backend.core.embedder import Embedder
from backend.core.faiss_store import FAISSStore
from backend.core.llm_provider import LLMProvider
from backend.core.prompt_builder import PromptBuilder
from backend.db.database import get_db
from backend.db.models import QueryRequest, QueryResponse
from backend.db.repository import PaperRepository
from backend.services.query_service import QueryService

router = APIRouter(prefix="/api")


def get_faiss_store() -> FAISSStore:
    from backend.main import faiss_store
    return faiss_store


def get_embedder() -> Embedder:
    from backend.main import embedder
    return embedder


def get_llm_provider() -> LLMProvider:
    from backend.main import llm_provider
    return llm_provider


@router.post("/query", response_model=QueryResponse)
async def query_papers(
    body: QueryRequest,
    db=Depends(get_db),
    store: FAISSStore = Depends(get_faiss_store),
    emb: Embedder = Depends(get_embedder),
    llm: LLMProvider = Depends(get_llm_provider),
):
    """根据问题检索相关 chunk，调用 LLM 生成答案。"""
    service = QueryService(store, emb, llm, db)
    try:
        return await service.query(body.question, body.paper_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"LLM or retrieval error: {e}")


@router.post("/query/stream")
async def query_papers_stream(
    body: QueryRequest,
    db=Depends(get_db),
    store: FAISSStore = Depends(get_faiss_store),
    emb: Embedder = Depends(get_embedder),
    llm: LLMProvider = Depends(get_llm_provider),
):
    """
    流式问答端点（SSE）。

    事件格式（每条以 \\n\\n 结尾）：
      data: {"type":"sources","sources":[...]}
      data: {"type":"delta","text":"..."}
      data: {"type":"done"}
    """
    from backend.config import TOP_K
    from backend.db.models import Source

    if not body.question.strip():
        raise HTTPException(status_code=400, detail="Question must not be empty")

    if body.paper_id is not None:
        repo = PaperRepository(db)
        paper = await repo.get_by_id(body.paper_id)
        if paper is None:
            raise HTTPException(status_code=404, detail=f"Paper not found: {body.paper_id}")

    query_vector = emb.embed([body.question])[0]
    results = store.search(query_vector, top_k=TOP_K, paper_id=body.paper_id)
    prompt = PromptBuilder().build(results, body.question)
    print("[PromptBuilder] prompt:\n", prompt, flush=True)

    sources = [
        Source(
            paper_id=r.paper_id,
            section=r.section,
            chunk_index=r.chunk_index,
            text=r.text,
            score=r.score,
        ).model_dump()
        for r in results
    ]

    async def event_generator() -> AsyncIterator[str]:
        # 1. Send sources first
        yield f"data: {json.dumps({'type': 'sources', 'sources': sources})}\n\n"
        # 2. Stream LLM text chunks
        full_answer = []
        async for chunk in llm.complete_stream(prompt):
            full_answer.append(chunk)
            yield f"data: {json.dumps({'type': 'delta', 'text': chunk})}\n\n"
        print("[LLM] answer:\n", "".join(full_answer), flush=True)
        # 3. Done signal
        yield "data: {\"type\":\"done\"}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
