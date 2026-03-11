from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import EMBEDDING_MODEL, FAISS_DIR, STORAGE_DIR
from backend.core.embedder import Embedder
from backend.core.faiss_store import FAISSStore
from backend.core.providers import create_llm_provider
from backend.db.database import init_db
from backend.routers import upload, query, papers

app = FastAPI(title="AI Research Paper Assistant")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:*", "http://127.0.0.1:*"],
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
