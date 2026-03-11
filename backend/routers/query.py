from fastapi import APIRouter, Depends, HTTPException

from backend.core.embedder import Embedder
from backend.core.faiss_store import FAISSStore
from backend.core.llm_provider import LLMProvider
from backend.db.database import get_db
from backend.db.models import QueryRequest, QueryResponse
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
    """
    根据问题检索相关 chunk，调用 LLM 生成答案。

    - question: 非空字符串
    - paper_id: 可选；指定时只在该论文内检索，省略则跨全库
    - 返回 {answer, sources}
    """
    service = QueryService(store, emb, llm, db)
    try:
        return await service.query(body.question, body.paper_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"LLM or retrieval error: {e}")
