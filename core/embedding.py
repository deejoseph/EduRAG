"""
EduRAG Embedding 模块
封装 SentenceTransformer，提供统一的文本向量化接口
"""

import logging
from typing import List, Optional

import torch
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

# BGE 模型官方推荐的查询前缀
BGE_QUERY_PREFIX = "为这个句子生成表示以用于检索中文文档："


class EmbeddingModel:
    """向量化模型封装"""

    def __init__(
        self,
        model_name: str = "BAAI/bge-base-zh-v1.5",
        device: Optional[str] = None,
    ):
        """
        初始化 Embedding 模型

        Args:
            model_name: HuggingFace 模型名称或本地路径
            device: 计算设备，None 时自动检测（cuda/cpu）
        """
        if device is None:
            device = "cuda" if torch.cuda.is_available() else "cpu"
        self.device = device
        self.model_name = model_name

        try:
            self._model = SentenceTransformer(model_name, device=device)
            logger.info(f"Embedding 模型加载成功: {model_name} (device: {device})")
        except Exception as e:
            logger.error(f"Embedding 模型加载失败: {e}")
            raise

    def encode(
        self,
        texts: List[str],
        batch_size: int = 32,
        show_progress_bar: bool = False,
    ) -> List[List[float]]:
        """
        将文本列表编码为向量列表（用于文档入库，不加查询前缀）

        Args:
            texts: 文本列表
            batch_size: 批处理大小
            show_progress_bar: 是否显示进度条

        Returns:
            向量列表，每个向量为 float 列表
        """
        embeddings = self._model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=show_progress_bar,
            normalize_embeddings=True,
        )
        return embeddings.tolist()

    def encode_query(self, text: str) -> List[float]:
        """
        编码单条查询文本（自动添加 BGE 查询前缀）

        Args:
            text: 查询文本

        Returns:
            向量（float 列表）
        """
        query_with_prefix = BGE_QUERY_PREFIX + text
        embedding = self._model.encode(
            [query_with_prefix],
            normalize_embeddings=True,
        )
        return embedding[0].tolist()

    def get_dimension(self) -> int:
        """返回向量维度"""
        return self._model.get_sentence_embedding_dimension()
