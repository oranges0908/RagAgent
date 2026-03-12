from backend.core.faiss_store import SearchResult

class PromptBuilder:
    """
    将检索结果和问题拼装成发送给 LLM 的 prompt。

    格式参考（system_design.md §6.3）：
        You are an AI research assistant. Answer the question based ONLY on the
        provided context. Cite sources using [N] notation.

        Context:
        [1] (Paper: <title>, Section: <section>)
        <chunk text>

        [2] ...

        Question: <question>

        Answer:
    """

    # 每个 context 块大致 token 估算系数（1 token ≈ 4 chars）
    _CHARS_PER_TOKEN = 4
    # prompt 中 context 部分最大 token 数（留出 question + 指令 + LLM 回复空间）
    _MAX_CONTEXT_TOKENS = 3000

    def build(self, chunks: list[SearchResult], question: str) -> str:
        """
        构建完整 prompt 字符串。

        :param chunks:   FAISSStore.search() 返回的检索结果（已按相似度排序）
        :param question: 用户的原始问题
        :return:         发送给 LLM 的完整 prompt

        实现要求：
        1. 将每个 chunk 格式化为编号块 [N]，包含 paper_id、section、text
        2. 若所有 chunk 文本总长超过 _MAX_CONTEXT_TOKENS * _CHARS_PER_TOKEN，
           按比例截断每个 chunk 的 text，确保总长不超限
        3. 拼接系统指令 + context 块 + 问题，返回完整字符串

        提示：
        - f"[{i+1}] (Paper: {r.paper_id}, Section: {r.section})\n{r.text}"
        - 截断时先算每个 chunk 可分配的字符数：max_chars // len(chunks)
        """
        # TODO: 实现 prompt 构建逻辑
        text_length_limit = self._MAX_CONTEXT_TOKENS * self._CHARS_PER_TOKEN // len(chunks)

        context = ""
        for index, chunk in enumerate(chunks):
            text = chunk.context_text    if len(chunk.context_text) <= text_length_limit else chunk.context_text[:text_length_limit]
            context += f"[{index + 1}] (Paper: {chunk.paper_id}, Section: {chunk.section})\n{text}\n\n"

        prompt = f"""You are an AI research assistant. Answer the question based ONLY on the provided context. Cite sources using [N] notation.

Context:
{context}
Question: {question}

Answer:"""
        # print("[PromptBuilder] prompt:\n", prompt, flush=True)
        return prompt
        raise NotImplementedError
