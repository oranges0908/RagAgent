from fastapi import APIRouter, Depends

from backend.db.database import get_db
from backend.db.models import Paper
from backend.db.repository import PaperRepository

router = APIRouter(prefix="/api")


@router.get("/papers", response_model=list[Paper])
async def list_papers(db=Depends(get_db)):
    """返回所有论文，按上传时间降序排列。"""
    repo = PaperRepository(db)
    return await repo.get_all()
