"""
EduRAG 重排序模块
使用 Cross-Encoder 对初检结果进行二次精排，提升检索精度
"""

import logging
from typing import List, Tuple

logger = logging.getLogger(__name__)


class CrossEncoderReranker:
    """
    基于 Cross-Encoder 的重排序器

    Cross-Encoder 同时输入 (query, document) 对进行打分，
    比 Bi-Encoder（向量检索）更精确，但计算成本更高。
    适合对 top-K 初检结果做二次精排。
    """

    def __init__(
        self,
        model_name: str = "BAAI/bge-reranker-base",
        device: str = None,
    ):
        """
        初始化重排序器

        Args:
            model_name: Cross-Encoder 模型名称
                推荐:
                - BAAI/bge-reranker-base (轻量，推荐)
                - BAAI/bge-reranker-large (更准但更慢)
            device: 运行设备 (cpu/cuda)，None 则自动选择
        """
        self.model_name = model_name
        self._device = device
        self._model = None

    def _load_model(self):
        """延迟加载模型（首次调用时才加载）"""
        if self._model is not None:
            return

        try:
            from sentence_transformers import CrossEncoder

            device = self._device
            if device is None:
                import torch
                device = 'cuda' if torch.cuda.is_available() else 'cpu'

            logger.info(f"加载 Cross-Encoder 重排序模型: {self.model_name} (device: {device})")
            self._model = CrossEncoder(
                self.model_name,
                device=device,
            )
            logger.info("Cross-Encoder 模型加载成功")

        except Exception as e:
            logger.error(f"Cross-Encoder 模型加载失败: {e}")
            self._model = None
            raise

    def predict(
        self,
        query: str,
        documents: List[str],
    ) -> List[float]:
        """
        对 (query, document) 对打分

        Args:
            query: 查询文本
            documents: 候选文档列表

        Returns:
            每个文档的相关性分数列表（0-1，越高越相关）
        """
        if not documents:
            return []

        self._load_model()

        # 构建 (query, doc) 对
        pairs = [[query, doc] for doc in documents]

        try:
            # Cross-Encoder 打分
            raw_scores = self._model.predict(pairs)

            # 将原始分数归一化到 0-1 范围（使用 sigmoid）
            import math
            normalized = [1.0 / (1.0 + math.exp(-s)) for s in raw_scores]

            return normalized

        except Exception as e:
            logger.error(f"Cross-Encoder 预测失败: {e}")
            # 降级：返回等分
            return [0.5] * len(documents)

    def rerank(
        self,
        query: str,
        ids: List[str],
        documents: List[str],
        metadatas: List[dict],
        original_scores: List[float],
        top_n: int = None,
        rerank_weight: float = 0.7,
    ) -> Tuple[List[str], List[str], List[dict], List[float]]:
        """
        重排序：对初检结果进行二次精排

        Args:
            query: 查询文本
            ids: 文档 ID 列表
            documents: 文档文本列表
            metadatas: 元数据列表
            original_scores: 原始检索分数
            top_n: 重排序后保留的数量（None=全部保留）
            rerank_weight: 重排序分数权重（0-1）
                - 0.0: 完全使用原始分数
                - 1.0: 完全使用重排序分数
                - 0.7: 推荐值，70% 重排序 + 30% 原始

        Returns:
            (ids, documents, metadatas, scores) 重排序后的四元组
        """
        if not documents or len(documents) <= 1:
            return ids, documents, metadatas, original_scores

        # Cross-Encoder 打分
        rerank_scores = self.predict(query, documents)

        # 混合分数 = rerank_weight * rerank_score + (1 - rerank_weight) * original_score
        combined_scores = [
            rerank_weight * rs + (1 - rerank_weight) * os
            for rs, os in zip(rerank_scores, original_scores)
        ]

        # 按混合分数降序排列
        paired = list(zip(combined_scores, ids, documents, metadatas))
        paired.sort(key=lambda x: x[0], reverse=True)

        # 拆分
        sorted_scores, sorted_ids, sorted_docs, sorted_metas = zip(*paired)
        sorted_scores = list(sorted_scores)
        sorted_ids = list(sorted_ids)
        sorted_docs = list(sorted_docs)
        sorted_metas = list(sorted_metas)

        # 截断
        if top_n and top_n < len(sorted_ids):
            sorted_ids = sorted_ids[:top_n]
            sorted_docs = sorted_docs[:top_n]
            sorted_metas = sorted_metas[:top_n]
            sorted_scores = sorted_scores[:top_n]

        logger.debug(
            f"重排序完成: {len(documents)} -> {len(sorted_ids)} 条, "
            f"分数范围 [{sorted_scores[-1]:.4f}, {sorted_scores[0]:.4f}]"
        )

        return sorted_ids, sorted_docs, sorted_metas, sorted_scores
