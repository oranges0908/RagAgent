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
        await db.commit()


def get_db_path() -> str:
    return str(DB_PATH)
