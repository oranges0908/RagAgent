from typing import Optional

import aiosqlite

from backend.db.models import Paper


class PaperRepository:
    def __init__(self, db: aiosqlite.Connection):
        self.db = db

    async def insert(self, paper: Paper) -> Paper:
        await self.db.execute(
            "INSERT INTO papers (id, title, filename, uploaded_at, chunk_count, status) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (paper.id, paper.title, paper.filename, paper.uploaded_at, paper.chunk_count, paper.status),
        )
        await self.db.commit()
        return paper

    async def get_all(self) -> list[Paper]:
        cursor = await self.db.execute(
            "SELECT id, title, filename, uploaded_at, chunk_count, status "
            "FROM papers ORDER BY uploaded_at DESC"
        )
        rows = await cursor.fetchall()
        return [Paper(id=r[0], title=r[1], filename=r[2], uploaded_at=r[3], chunk_count=r[4], status=r[5]) for r in rows]

    async def get_by_id(self, id: str) -> Optional[Paper]:
        cursor = await self.db.execute(
            "SELECT id, title, filename, uploaded_at, chunk_count, status FROM papers WHERE id = ?",
            (id,),
        )
        row = await cursor.fetchone()
        if row is None:
            return None
        return Paper(id=row[0], title=row[1], filename=row[2], uploaded_at=row[3], chunk_count=row[4], status=row[5])

    async def update_status(self, id: str, status: str, chunk_count: Optional[int] = None) -> None:
        if chunk_count is not None:
            await self.db.execute(
                "UPDATE papers SET status = ?, chunk_count = ? WHERE id = ?",
                (status, chunk_count, id),
            )
        else:
            await self.db.execute(
                "UPDATE papers SET status = ? WHERE id = ?",
                (status, id),
            )
        await self.db.commit()

    async def delete(self, id: str) -> None:
        await self.db.execute("DELETE FROM papers WHERE id = ?", (id,))
        await self.db.commit()
