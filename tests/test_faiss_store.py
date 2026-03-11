import numpy as np
import pytest

from backend.core.faiss_store import FAISSStore, SearchResult

DIM = 64  # 测试用低维向量，避免依赖真实 embedding 模型


def make_vectors(n: int, dim: int = DIM, seed: int = 0) -> np.ndarray:
    rng = np.random.default_rng(seed)
    return rng.random((n, dim)).astype(np.float32)


def make_metadata(n: int, paper_id: str = "paper-1") -> list[dict]:
    return [
        {"chunk_index": i, "section": "Abstract", "text": f"chunk text {i}"}
        for i in range(n)
    ]


@pytest.fixture
def store():
    return FAISSStore()


# ---------- add ----------

def test_add_stores_in_memory(store):
    """add 后 paper_id 应出现在内部缓存中"""
    vecs = make_vectors(5)
    store.add("paper-1", vecs, make_metadata(5))
    assert "paper-1" in store._indexes
    assert store._indexes["paper-1"].ntotal == 5
    assert len(store._metadata["paper-1"]) == 5


def test_add_overwrites_existing(store):
    """同一 paper_id 再次 add 应覆盖旧数据"""
    store.add("paper-1", make_vectors(3), make_metadata(3))
    store.add("paper-1", make_vectors(7), make_metadata(7))
    assert store._indexes["paper-1"].ntotal == 7


# ---------- save / load ----------

def test_save_creates_files(store, tmp_path, monkeypatch):
    """save 应在 FAISS_DIR 下写出 .index 和 .meta.json"""
    monkeypatch.setattr("backend.core.faiss_store.FAISS_DIR", tmp_path)
    store.add("paper-1", make_vectors(4), make_metadata(4))
    store.save("paper-1")
    assert (tmp_path / "paper-1.index").exists()
    assert (tmp_path / "paper-1.meta.json").exists()


def test_save_then_load_search_consistent(store, tmp_path, monkeypatch):
    """add → save → 新 store load → search 结果一致"""
    monkeypatch.setattr("backend.core.faiss_store.FAISS_DIR", tmp_path)

    vecs = make_vectors(10)
    meta = make_metadata(10)
    store.add("paper-1", vecs, meta)
    store.save("paper-1")

    store2 = FAISSStore()
    monkeypatch.setattr("backend.core.faiss_store.FAISS_DIR", tmp_path)
    store2.load("paper-1")

    query = make_vectors(1, seed=99)
    results = store2.search(query[0], top_k=3, paper_id="paper-1")
    assert len(results) == 3
    assert all(isinstance(r, SearchResult) for r in results)


def test_load_all(store, tmp_path, monkeypatch):
    """load_all 应自动加载目录下所有 .index 文件"""
    monkeypatch.setattr("backend.core.faiss_store.FAISS_DIR", tmp_path)
    for pid in ["p1", "p2", "p3"]:
        store.add(pid, make_vectors(5), make_metadata(5, paper_id=pid))
        store.save(pid)

    store2 = FAISSStore()
    monkeypatch.setattr("backend.core.faiss_store.FAISS_DIR", tmp_path)
    store2.load_all()
    assert set(store2._indexes.keys()) == {"p1", "p2", "p3"}


# ---------- search ----------

def test_search_single_paper(store):
    """指定 paper_id 时只在该论文内检索"""
    vecs = make_vectors(10)
    store.add("paper-1", vecs, make_metadata(10))
    query = vecs[0]  # 查询向量与第 0 条完全一致，应排第一
    results = store.search(query, top_k=3, paper_id="paper-1")
    assert len(results) == 3
    assert results[0].chunk_index == 0
    assert results[0].score < results[1].score   # 按 L2 距离升序


def test_search_cross_papers(store):
    """paper_id=None 时跨所有论文检索，结果数 <= top_k"""
    store.add("paper-1", make_vectors(5, seed=1), make_metadata(5, "paper-1"))
    store.add("paper-2", make_vectors(5, seed=2), make_metadata(5, "paper-2"))
    query = make_vectors(1, seed=99)[0]
    results = store.search(query, top_k=3)
    assert len(results) <= 3
    assert all(isinstance(r, SearchResult) for r in results)


def test_search_returns_correct_chunk(store):
    """查询向量与 chunk 7 完全一致时，top-1 应返回 chunk_index=7"""
    vecs = make_vectors(10)
    store.add("paper-1", vecs, make_metadata(10))
    results = store.search(vecs[7], top_k=1, paper_id="paper-1")
    assert results[0].chunk_index == 7
    assert results[0].score == pytest.approx(0.0, abs=1e-5)


def test_search_result_fields(store):
    """SearchResult 包含所有必要字段且类型正确"""
    store.add("paper-1", make_vectors(5), make_metadata(5))
    results = store.search(make_vectors(1)[0], top_k=1, paper_id="paper-1")
    r = results[0]
    assert isinstance(r.paper_id, str)
    assert isinstance(r.chunk_index, int)
    assert isinstance(r.section, str)
    assert isinstance(r.text, str)
    assert isinstance(r.score, float)
