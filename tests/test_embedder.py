import numpy as np
import pytest

from backend.config import EMBEDDING_MODEL
from backend.core.embedder import Embedder


@pytest.fixture(scope="module")
def embedder():
    return Embedder(EMBEDDING_MODEL)


def test_embed_shape(embedder):
    """embed 5 条文本，返回 shape (5, dim)"""
    texts = ["hello", "world", "foo", "bar", "baz"]
    result = embedder.embed(texts)
    assert result.shape == (5, embedder.dim)


def test_embed_dtype(embedder):
    """返回值应为 float32"""
    result = embedder.embed(["test sentence"])
    assert result.dtype == np.float32


def test_embed_empty(embedder):
    """空列表应返回 shape (0, dim) 的数组"""
    result = embedder.embed([])
    assert result.shape == (0, embedder.dim)


def test_dim_positive(embedder):
    """dim 应为正整数"""
    assert isinstance(embedder.dim, int)
    assert embedder.dim > 0


def test_different_texts_different_vectors(embedder):
    """语义不同的文本，向量不应完全相同"""
    v1 = embedder.embed(["The cat sat on the mat."])
    v2 = embedder.embed(["Quantum physics is complex."])
    assert not np.allclose(v1, v2)
