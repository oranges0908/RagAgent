from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse

from backend.config import MAX_UPLOAD_BYTES
from backend.db.database import get_db
from backend.db.models import Paper
from backend.core.faiss_store import FAISSStore
from backend.services.ingestion import IngestionService

router = APIRouter(prefix="/api")


def get_faiss_store() -> FAISSStore:
    """返回应用启动时初始化的全局 FAISSStore 实例（在 main.py 中注入）。"""
    from backend.main import faiss_store
    return faiss_store


@router.post("/upload", response_model=Paper)
async def upload_pdf(
    file: UploadFile = File(...),
    db=Depends(get_db),
    store: FAISSStore = Depends(get_faiss_store),
):
    """
    上传 PDF 文件，触发摄入流水线。

    - 文件类型：仅接受 .pdf
    - 文件大小：最大 20MB
    - 返回：写入 DB 的 Paper 对象
    """
    # 校验文件类型
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")

    # 读取并校验大小
    file_bytes = await file.read()
    if len(file_bytes) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size is {MAX_UPLOAD_BYTES // (1024*1024)}MB.",
        )

    service = IngestionService(db, store)
    try:
        paper = await service.ingest(file_bytes, file.filename)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {e}")

    return paper
