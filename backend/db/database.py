import aiosqlite

from backend.config import DB_PATH


async def init_db() -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("PRAGMA journal_mode=WAL")
        await db.execute("""
            CREATE TABLE IF NOT EXISTS papers (
                id          TEXT PRIMARY KEY,
                title       TEXT NOT NULL,
                filename    TEXT NOT NULL,
                uploaded_at TEXT NOT NULL,
                chunk_count INTEGER NOT NULL DEFAULT 0,
                status      TEXT NOT NULL DEFAULT 'processing'
                            CHECK(status IN ('uploading','processing','ready','error'))
            )
        """)
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_papers_uploaded_at ON papers(uploaded_at DESC)
        """)
        # 兼容旧数据库：file_hash 列可能不存在
        try:
            await db.execute("ALTER TABLE papers ADD COLUMN file_hash TEXT")
        except Exception:
            pass  # 列已存在，忽略
        await db.commit()


def get_db_path() -> str:
    return str(DB_PATH)


async def get_db():
    """FastAPI 依赖：提供一个 aiosqlite 连接，请求结束后自动关闭。"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("PRAGMA journal_mode=WAL")
        yield db
