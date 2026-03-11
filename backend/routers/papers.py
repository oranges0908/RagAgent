from fastapi import APIRouter, Depends, HTTPException, Response

from backend.config import FAISS_DIR
from backend.core.faiss_store import FAISSStore
from backend.db.database import get_db
from backend.db.models import Paper
from backend.db.repository import PaperRepository

router = APIRouter(prefix="/api")


def get_faiss_store() -> FAISSStore:
    from backend.main import faiss_store
    return faiss_store


@router.get("/papers", response_model=list[Paper])
async def list_papers(db=Depends(get_db)):
    """返回所有论文，按上传时间降序排列。"""
    repo = PaperRepository(db)
    return await repo.get_all()


@router.delete("/papers/{paper_id}", status_code=204)
async def delete_paper(
    paper_id: str,
    db=Depends(get_db),
    store: FAISSStore = Depends(get_faiss_store),
):
    """删除论文及其向量索引。"""
    repo = PaperRepository(db)
    paper = await repo.get_by_id(paper_id)
    if paper is None:
        raise HTTPException(status_code=404, detail=f"Paper not found: {paper_id}")

    # SQLite
    await repo.delete(paper_id)

    # FAISS files
    for suffix in (".index", ".meta.json"):
        path = FAISS_DIR / f"{paper_id}{suffix}"
        path.unlink(missing_ok=True)

    # In-memory cache
    store.remove(paper_id)

    return Response(status_code=204)
