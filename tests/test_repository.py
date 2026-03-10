import pytest
import pytest_asyncio
import aiosqlite

from backend.db.models import Paper
from backend.db.repository import PaperRepository


CREATE_TABLE = """
CREATE TABLE papers (
    id          TEXT PRIMARY KEY,
    title       TEXT NOT NULL,
    filename    TEXT NOT NULL,
    uploaded_at TEXT NOT NULL,
    chunk_count INTEGER NOT NULL DEFAULT 0,
    status      TEXT NOT NULL DEFAULT 'processing'
                CHECK(status IN ('uploading','processing','ready','error'))
)
"""


@pytest_asyncio.fixture
async def repo():
    async with aiosqlite.connect(":memory:") as db:
        await db.execute("PRAGMA journal_mode=WAL")
        await db.execute(CREATE_TABLE)
        await db.commit()
        yield PaperRepository(db)


def make_paper(**kwargs) -> Paper:
    defaults = dict(
        id="test-uuid-1",
        title="Test Paper",
        filename="test.pdf",
        uploaded_at="2026-03-09T10:00:00Z",
        chunk_count=0,
        status="processing",
    )
    defaults.update(kwargs)
    return Paper(**defaults)


@pytest.mark.asyncio
async def test_insert_and_get_by_id(repo):
    paper = make_paper()
    await repo.insert(paper)
    result = await repo.get_by_id(paper.id)
    assert result is not None
    assert result.id == paper.id
    assert result.title == paper.title
    assert result.filename == paper.filename


@pytest.mark.asyncio
async def test_get_all_ordering(repo):
    p1 = make_paper(id="uuid-1", uploaded_at="2026-03-09T09:00:00Z")
    p2 = make_paper(id="uuid-2", uploaded_at="2026-03-09T10:00:00Z")
    await repo.insert(p1)
    await repo.insert(p2)
    papers = await repo.get_all()
    assert len(papers) == 2
    assert papers[0].id == "uuid-2"  # DESC order


@pytest.mark.asyncio
async def test_get_by_id_not_found(repo):
    result = await repo.get_by_id("nonexistent")
    assert result is None


@pytest.mark.asyncio
async def test_update_status(repo):
    paper = make_paper()
    await repo.insert(paper)
    await repo.update_status(paper.id, "ready", chunk_count=42)
    result = await repo.get_by_id(paper.id)
    assert result.status == "ready"
    assert result.chunk_count == 42


@pytest.mark.asyncio
async def test_update_status_without_chunk_count(repo):
    paper = make_paper()
    await repo.insert(paper)
    await repo.update_status(paper.id, "error")
    result = await repo.get_by_id(paper.id)
    assert result.status == "error"
    assert result.chunk_count == 0


@pytest.mark.asyncio
async def test_delete(repo):
    paper = make_paper()
    await repo.insert(paper)
    await repo.delete(paper.id)
    result = await repo.get_by_id(paper.id)
    assert result is None
