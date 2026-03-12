import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import faiss
import numpy as np

from backend.config import FAISS_DIR


@dataclass
class SearchResult:
    paper_id: str       # 来源论文 ID
    chunk_index: int    # chunk 在原文中的序号
    section: str        # 所属章节名
    text: str           # 命中 chunk 原文（用于 LLM prompt）
    score: float        # 相似度分数（L2 距离，越小越相似）
    context_text: str = ""  # 扩展上下文（±2 相邻 chunk，用于前端展示）


class FAISSStore:
    def __init__(self):
        # key: paper_id -> faiss.IndexFlatL2
        self._indexes: dict[str, faiss.IndexFlatL2] = {}
        # key: paper_id -> list[dict]，每个 dict 对应一个 chunk 的元数据
        # 元数据字段与 SearchResult 对应：chunk_index, section, text
        self._metadata: dict[str, list[dict]] = {}

    def add(self, paper_id: str, vectors: np.ndarray, metadata_list: list[dict]) -> None:
        """
        将论文的向量和元数据写入内存。

        :param paper_id:      论文 UUID
        :param vectors:       shape=(N, dim) float32 numpy 数组
        :param metadata_list: 长度为 N 的列表，每个元素是一个 dict，
                              至少包含 chunk_index, section, text

        提示：
        - 用 faiss.IndexFlatL2(dim) 创建索引（dim = vectors.shape[1]）
        - 调用 index.add(vectors) 写入向量
        - 将 index 和 metadata_list 分别存入 self._indexes / self._metadata
        - 若 paper_id 已存在，直接覆盖
        """
        # TODO: 实现 add 逻辑
        self._indexes[paper_id] = faiss.IndexFlatL2(vectors.shape[1])
        self._indexes[paper_id].add(vectors)
        self._metadata[paper_id] = metadata_list

    def save(self, paper_id: str) -> None:
        """
        将内存中的索引和元数据持久化到磁盘。

        写入路径（均在 FAISS_DIR 下）：
          - {paper_id}.index      → faiss 二进制索引文件
          - {paper_id}.meta.json  → JSON 格式的 metadata_list

        提示：
        - faiss.write_index(index, str(path))
        - json.dumps(metadata_list, ensure_ascii=False)
        - paper_id 必须已在 self._indexes 中，否则抛 KeyError
        """
        # TODO: 实现 save 逻辑
        if paper_id not in self._indexes:
            raise KeyError

        faiss.write_index(self._indexes[paper_id], str(FAISS_DIR / f"{paper_id}.index"))
        with open(str(FAISS_DIR / f"{paper_id}.meta.json"), "w") as f:
            json.dump(self._metadata[paper_id], f, ensure_ascii=False)


    def load(self, paper_id: str) -> None:
        """
        从磁盘读取索引和元数据到内存缓存。

        读取路径（均在 FAISS_DIR 下）：
          - {paper_id}.index
          - {paper_id}.meta.json

        提示：
        - faiss.read_index(str(path))
        - 若文件不存在，抛 FileNotFoundError
        - 加载后更新 self._indexes 和 self._metadata
        """
        # TODO: 实现 load 逻辑
        index_file = str(FAISS_DIR / f"{paper_id}.index")
        if not Path(index_file).exists():
            raise FileNotFoundError(index_file)

        metadata_file = str(FAISS_DIR / f"{paper_id}.meta.json")
        if not Path(metadata_file).exists():
            raise FileNotFoundError(metadata_file)


        self._indexes[paper_id]=faiss.read_index(index_file)

        with open(metadata_file, "r") as f:
            self._metadata[paper_id] = json.load(f)

    def load_all(self) -> None:
        """
        扫描 FAISS_DIR，自动加载所有 .index 文件。

        提示：
        - 遍历 FAISS_DIR.glob("*.index")
        - 每个文件的 stem 即为 paper_id，调用 self.load(paper_id)
        - 若某个 paper_id 的 .meta.json 不存在，跳过并打印警告
        """
        # TODO: 实现 load_all 逻辑
        for index_file in FAISS_DIR.glob("*.index"):
            paper_id = index_file.stem
            self.load(paper_id)

    def search(
        self,
        query_vector: np.ndarray,
        top_k: int,
        paper_id: Optional[str] = None,
    ) -> list[SearchResult]:
        """
        在向量索引中检索最相似的 top_k 个 chunk。

        :param query_vector: shape=(dim,) 或 (1, dim) 的 float32 数组
        :param top_k:        返回结果数量
        :param paper_id:     指定论文 ID 时只在该论文内检索；
                             为 None 时跨所有已加载论文检索

        :return: 按 score 升序（L2 距离越小越相关）排列的 SearchResult 列表

        提示：
        - 将 query_vector reshape 为 (1, dim)，确保 dtype=float32
        - 对每个目标 index 调用 index.search(query, top_k) → distances, indices
        - indices 中 -1 表示无效结果，需跳过
        - 跨论文检索时，对所有论文分别 search，合并结果后按 score 排序取前 top_k
        - score 直接使用 L2 距离（distances[0][i]）
        """
        # TODO: 实现 search 逻辑
        if query_vector.ndim == 1:
            query_vector = query_vector.reshape(1, query_vector.shape[0])

        rc = []

        for paper in self._indexes:
            if paper_id is not None and paper != paper_id:
                continue

            distances, indices = self._indexes[paper].search(query_vector, k=top_k)
            for pos, idx in enumerate(indices[0]):
                if idx == -1:
                    continue
                meta = self._metadata[paper]
                matched = meta[idx]
                section = matched["section"]

                # 扩展上下文：取 ±2 相邻 chunk（同 section）
                window = meta[max(0, idx - 2): idx + 3]
                context_chunks = [c for c in window if c["section"] == section]
                context_chunks.sort(key=lambda c: c["char_start"])
                context_text = " ".join(c["text"] for c in context_chunks)

                sr = SearchResult(
                    paper_id=paper,
                    chunk_index=matched["chunk_index"],
                    section=section,
                    text=matched["text"],
                    score=float(distances[0][pos]),
                    context_text=context_text,
                )
                rc.append(sr)

        return sorted(rc, key=lambda sr: sr.score, reverse=False)[:top_k]

    def remove(self, paper_id: str) -> None:
        """从内存缓存中移除论文的索引和元数据（文件删除由调用方负责）。"""
        self._indexes.pop(paper_id, None)
        self._metadata.pop(paper_id, None)