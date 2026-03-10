from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import FAISS_DIR, STORAGE_DIR
from backend.db.database import init_db

app = FastAPI(title="AI Research Paper Assistant")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:*", "http://127.0.0.1:*"],
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    STORAGE_DIR.mkdir(exist_ok=True)
    FAISS_DIR.mkdir(exist_ok=True)
    await init_db()


@app.get("/")
async def root():
    return {"status": "ok"}
