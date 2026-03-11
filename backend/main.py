from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import FAISS_DIR, STORAGE_DIR
from backend.core.faiss_store import FAISSStore
from backend.db.database import init_db
from backend.routers import upload

app = FastAPI(title="AI Research Paper Assistant")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:*", "http://127.0.0.1:*"],
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
)

# 全局 FAISSStore 实例，startup 时加载磁盘索引，供各 router 共享
faiss_store = FAISSStore()

app.include_router(upload.router)


@app.on_event("startup")
async def startup():
    STORAGE_DIR.mkdir(exist_ok=True)
    FAISS_DIR.mkdir(exist_ok=True)
    await init_db()
    faiss_store.load_all()  # 自动加载 storage/faiss/ 下所有已有索引


@app.get("/")
async def root():
    return {"status": "ok"}
