from typing import Optional

import aiosqlite

from backend.config import TOP_K
from backend.core.embedder import Embedder
from backend.core.faiss_store import FAISSStore
from backend.core.llm_provider import LLMProvider
from backend.core.prompt_builder import PromptBuilder
from backend.db.models import QueryResponse, Source
from backend.db.repository import PaperRepository


class QueryService:
    def __init__(
        self,
        faiss_store: FAISSStore,
        embedder: Embedder,
        llm_provider: LLMProvider,
        db: aiosqlite.Connection,
    ):
        self.faiss_store = faiss_store
        self.embedder = embedder
        self.llm = llm_provider
        self.prompt_builder = PromptBuilder()
        self.repo = PaperRepository(db)

    async def query(
        self,
        question: str,
        paper_id: Optional[str] = None,
    ) -> QueryResponse:
        """
        完整的 RAG 问答流程。

        1. embed question
        2. FAISSStore.search(top_k, paper_id?)
        3. PromptBuilder.build(chunks, question)
        4. LLMProvider.complete(prompt) → answer text
        5. 组装 QueryResponse（answer + sources）

        :param question: 用户的自然语言问题
        :param paper_id: 可选；指定时只在该论文内检索
        :return:         QueryResponse，包含 answer 和 sources 列表
        :raises ValueError: question 为空时
        :raises KeyError:   paper_id 指定但论文不存在时
        """
        if not question.strip():
            raise ValueError("Question must not be empty")

        # 若指定 paper_id，校验论文存在
        if paper_id is not None:
            paper = await self.repo.get_by_id(paper_id)
            if paper is None:
                raise KeyError(f"Paper not found: {paper_id}")

        # 1. 将问题向量化
        query_vector = self.embedder.embed([question])[0]  # shape: (dim,)

        # 2. 向量检索
        results = self.faiss_store.search(query_vector, top_k=TOP_K, paper_id=paper_id)

        # 3. 构建 prompt
        prompt = self.prompt_builder.build(results, question)

        # 4. 调用 LLM
        answer = await self.llm.complete(prompt)

        # 5. 组装 sources
        sources = [
            Source(
                paper_id=r.paper_id,
                section=r.section,
                chunk_index=r.chunk_index,
                text=r.text,
                score=r.score,
            )
            for r in results
        ]

        return QueryResponse(answer=answer, sources=sources)
