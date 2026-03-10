import re
from dataclasses import dataclass


# 句子边界正则：`. ? !` 后跟空格或字符串末尾
_SENTENCE_END_RE = re.compile(r'(?<=[.?!])\s+')


@dataclass
class Chunk:
    text: str           # chunk 的文本内容
    section: str        # 所属章节名，如 "Abstract"、"Introduction"
    chunk_index: int    # 在该 section 内的序号（从 0 开始）
    char_start: int     # 在原始 text 中的起始字符位置
    char_end: int       # 在原始 text 中的结束字符位置（不含）


class TextChunker:
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 100):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk(self, text: str, section: str) -> list[Chunk]:
        """
        将 text 按滑动窗口切分为 Chunk 列表。

        算法要点：
        1. 用 _SENTENCE_END_RE 将 text 拆分为句子列表（保留位置信息）
        2. 滑动窗口：
           - 向窗口累加句子，直到超过 chunk_size
           - 超出时，把当前窗口内容作为一个 Chunk 输出
           - 回退 chunk_overlap 个字符，继续下一个窗口
        3. 循环结束后，若窗口中还有剩余文本，生成最后一个 Chunk
        4. 每个 Chunk 需正确记录 char_start / char_end（相对于原始 text）

        提示：
        - 句子边界切分可用 re.split(pattern, text) 配合 re.finditer 获取每段的起始偏移
        - chunk_overlap 表示相邻 chunk 之间重叠的字符数，不是句子数
        - 如果 text 比 chunk_size 短，直接返回一个 Chunk 即可

        :param text:    待切分的纯文本（一个 section 的完整内容）
        :param section: 该文本所属的章节名
        :return:        Chunk 列表，chunk_index 从 0 连续递增
        """
        # TODO: 在这里实现切分逻辑
        result = []

        sentences_iter = re.finditer(_SENTENCE_END_RE, text)

        chunk_index = 0
        new_chunk = Chunk(section=section,char_start=0,char_end=0,text="",chunk_index=chunk_index)
        for sentence in sentences_iter:
            if sentence.start() - new_chunk.char_start  > self.chunk_size:
                # 导出一个chunk
                result.append(new_chunk)
                chunk_index += 1

                # 初始化新chunk
                start = new_chunk.char_end - self.chunk_overlap if new_chunk.char_end - self.chunk_overlap > 0 else 0
                new_chunk = Chunk(section=section, char_start=start, char_end=sentence.end(), chunk_index=chunk_index,text=text[start:sentence.end()])
            else:
                new_chunk.text += text[new_chunk.char_end:sentence.end()]
                new_chunk.char_end = sentence.end()

        # 处理最后一句
        new_chunk.text += text[new_chunk.char_end:]
        new_chunk.char_end = len(text)
        # 处理最后一个chunk
        result.append(new_chunk)

        return result
