import pytest
from backend.core.text_chunker import TextChunker, Chunk

# 用于测试的基准参数
CHUNK_SIZE = 100
OVERLAP = 20


@pytest.fixture
def chunker():
    return TextChunker(chunk_size=CHUNK_SIZE, chunk_overlap=OVERLAP)


def test_short_text_single_chunk(chunker):
    """文本短于 chunk_size 时，应只产生一个 chunk"""
    text = "This is a short sentence."
    chunks = chunker.chunk(text, "Abstract")
    assert len(chunks) == 1
    assert chunks[0].text == text
    assert chunks[0].chunk_index == 0


def test_chunk_index_sequential(chunker):
    """chunk_index 应从 0 开始连续递增"""
    text = ("Hello world. " * 20).strip()
    chunks = chunker.chunk(text, "Body")
    for i, c in enumerate(chunks):
        assert c.chunk_index == i


def test_char_start_end_correct(chunker):
    """char_start / char_end 应对应原始 text 中的实际位置"""
    text = ("Alpha beta gamma. " * 15).strip()
    chunks = chunker.chunk(text, "Introduction")
    for c in chunks:
        assert text[c.char_start:c.char_end] == c.text


def test_overlap_chars(chunker):
    """相邻两个 chunk 的重叠字符数应 >= chunk_overlap（最后一个 chunk 除外）"""
    text = ("Sentence number one. Sentence number two. " * 10).strip()
    chunks = chunker.chunk(text, "Methods")
    for i in range(len(chunks) - 1):
        overlap = len(set(range(chunks[i].char_start, chunks[i].char_end)) &
                      set(range(chunks[i + 1].char_start, chunks[i + 1].char_end)))
        assert overlap >= OVERLAP, f"Chunk {i} and {i+1} overlap {overlap} chars, expected >= {OVERLAP}"


def test_no_word_break_at_boundary(chunker):
    """chunk 边界不应在单词中间切断（首尾不含半个单词）"""
    text = "The quick brown fox jumps over the lazy dog. " * 10
    chunks = chunker.chunk(text, "Body")
    for c in chunks:
        # chunk 文本首字符不应是字母且前一字符也是字母（即切断了单词）
        start = c.char_start
        if start > 0:
            assert not (text[start].isalpha() and text[start - 1].isalpha()), \
                f"Word break at char_start={start}: '...{text[start-3:start+3]}...'"


def test_section_preserved(chunker):
    """所有 chunk 的 section 字段应与传入值一致"""
    text = ("Some text. " * 20).strip()
    chunks = chunker.chunk(text, "Conclusion")
    for c in chunks:
        assert c.section == "Conclusion"


def test_chunk_is_dataclass(chunker):
    """返回值应为 Chunk dataclass 实例"""
    chunks = chunker.chunk("A short text.", "Abstract")
    assert len(chunks) >= 1
    c = chunks[0]
    assert isinstance(c, Chunk)
    assert isinstance(c.text, str)
    assert isinstance(c.section, str)
    assert isinstance(c.chunk_index, int)
    assert isinstance(c.char_start, int)
    assert isinstance(c.char_end, int)
