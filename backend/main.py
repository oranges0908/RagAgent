import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.config import EMBEDDING_MODEL, FAISS_DIR, STORAGE_DIR
from backend.core.embedder import Embedder
from backend.core.faiss_store import FAISSStore
from backend.core.providers import create_llm_provider
from backend.db.database import init_db
from backend.routers import upload, query, papers

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="AI Research Paper Assistant")


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled exception on %s %s", request.method, request.url)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
)

# 全局单例，startup 时初始化，供各 router 通过依赖注入共享
faiss_store = FAISSStore()
embedder = Embedder(EMBEDDING_MODEL)       # 加载 sentence-transformers 模型
llm_provider = create_llm_provider()      # 根据 config.LLM_PROVIDER 创建

app.include_router(upload.router)
app.include_router(query.router)
app.include_router(papers.router)


@app.on_event("startup")
async def startup():
    STORAGE_DIR.mkdir(exist_ok=True)
    FAISS_DIR.mkdir(exist_ok=True)
    await init_db()
    faiss_store.load_all()  # 自动加载 storage/faiss/ 下所有已有索引


@app.get("/")
async def root():
    return {"status": "ok"}
