import uuid
from datetime import datetime, timezone

import aiosqlite

from backend.config import CHUNK_SIZE, CHUNK_OVERLAP, EMBEDDING_MODEL
from backend.core.embedder import Embedder
from backend.core.faiss_store import FAISSStore
from backend.core.pdf_extractor import PDFExtractor
from backend.core.text_chunker import TextChunker
from backend.db.models import Paper
from backend.db.repository import PaperRepository
from dataclasses import  asdict

class IngestionService:
    def __init__(self, db: aiosqlite.Connection, faiss_store: FAISSStore):
        self.repo = PaperRepository(db)
        self.faiss_store = faiss_store
        self.pdf_extractor = PDFExtractor()
        self.chunker = TextChunker(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
        self.embedder = Embedder(EMBEDDING_MODEL)

    async def ingest(self, file_bytes: bytes, filename: str, file_hash: str | None = None) -> Paper:
        """
        完整的 PDF 摄入流水线：提取 → 分块 → Embedding → 写入 FAISS + SQLite。

        :param file_bytes: 上传的 PDF 原始字节
        :param filename:   原始文件名，用于生成 title 和记录元数据
        :return:           已写入 DB 的 Paper 对象（status='ready'）

        流程：
        1. 生成 UUID，以 status='processing' 写入 DB（已实现）
        2. ← 你来实现：PDF 提取 → 分块 → embed → FAISSStore.add + save
           - PDFExtractor.extract(file_bytes) -> list[PageSection]
           - 对每个 section 调用 TextChunker.chunk(section.text, section.section)
           - 收集所有 Chunk，拼出 texts 列表和 metadata_list
             metadata_list 中每条 dict 需包含：chunk_index, section, text
           - Embedder.embed(texts) -> vectors (shape N×dim)
           - FAISSStore.add(paper_id, vectors, metadata_list)
           - FAISSStore.save(paper_id)
        3. 更新 DB status='ready', chunk_count=总 chunk 数（已实现）
        4. 任何异常 → 更新 DB status='error' 后重新抛出（已实现）
        """
        # 1. 生成元数据，写入 DB（status=processing）
        paper_id = str(uuid.uuid4())
        title = filename.removesuffix(".pdf")
        now = datetime.now(timezone.utc).isoformat()
        paper = Paper(
            id=paper_id,
            title=title,
            filename=filename,
            uploaded_at=now,
            chunk_count=0,
            status="processing",
            file_hash=file_hash,
        )
        await self.repo.insert(paper)

        try:
            # 2. TODO: PDF 提取 → 分块 → embed → FAISSStore.add + save
            #    完成后将总 chunk 数赋给 chunk_count
            # 提取所有 section，收集全部 chunk 后一次性 embed + add
            page_sections = self.pdf_extractor.extract(file_bytes)
            all_chunks = []
            for section in page_sections:
                all_chunks.extend(self.chunker.chunk(section.text, section.section))

            chunk_count = len(all_chunks)
            texts = [c.text for c in all_chunks]
            metadata_list = [asdict(c) for c in all_chunks]
            vectors = self.embedder.embed(texts)

            self.faiss_store.add(paper_id, vectors, metadata_list)
            self.faiss_store.save(paper_id)

            # 3. 更新 DB：ready
            await self.repo.update_status(paper_id, "ready", chunk_count=chunk_count)

        except Exception:
            # 4. 任何错误：更新 DB status=error，重新抛出
            await self.repo.update_status(paper_id, "error")
            raise

        return await self.repo.get_by_id(paper_id)
