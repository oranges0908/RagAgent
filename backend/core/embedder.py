import numpy as np
from sentence_transformers import SentenceTransformer


class Embedder:
    def __init__(self, model_name: str):
        """
        加载 sentence-transformers 模型，并记录向量维度。

        :param model_name: 模型名称，如 "all-MiniLM-L6-v2"
                           （与 config.py 中的 EMBEDDING_MODEL 一致）

        提示：
        - 用 SentenceTransformer(model_name) 加载模型
        - 通过 encode 一条空字符串或查看 model.get_sentence_embedding_dimension()
          来获取 dim，并保存到 self.dim
        """
        # TODO: 加载模型，记录 self.model 和 self.dim
        self.model = SentenceTransformer(model_name)
        self.dim = self.model.get_sentence_embedding_dimension()
        print("Embedder dimension",self.dim)

    def embed(self, texts: list[str]) -> np.ndarray:
        """
        批量将文本列表转为向量矩阵。

        :param texts: 文本列表，长度为 N
        :return:      shape=(N, dim) 的 float32 numpy 数组

        提示：
        - 使用 self.model.encode(texts, batch_size=32, show_progress_bar=False)
        - 返回值需确保 dtype 为 np.float32（sentence-transformers 默认已是 float32）
        - 若 texts 为空列表，返回 shape=(0, self.dim) 的空数组
        """
        # TODO: 实现批量 embed
        if not texts:
            return np.zeros((0, self.dim))
        embeddings = self.model.encode(texts, batch_size=32, show_progress_bar=False)
        return np.array(embeddings).astype(np.float32)
        raise NotImplementedError
