"""
EduRAG 检索器模块
支持单集合/多集合检索，预留 cross-encoder 重排序接口
"""

import logging
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

from core.embedding import EmbeddingModel
from core.db_manager import EduRAGDatabase

logger = logging.getLogger(__name__)


@dataclass
class RetrievalResult:
    """检索结果"""
    ids: List[str] = field(default_factory=list)
    documents: List[str] = field(default_factory=list)
    metadatas: List[Dict[str, Any]] = field(default_factory=list)
    scores: List[float] = field(default_factory=list)
    source_collection: str = ""


class Retriever:
    """向量检索器"""

    def __init__(
        self,
        db: EduRAGDatabase,
        embedder: EmbeddingModel,
        reranker=None,
        enable_rerank: bool = False,
    ):
        """
        初始化检索器

        Args:
            db: 数据库实例
            embedder: 向量化模型实例
            reranker: 重排序模型实例（CrossEncoderReranker）
            enable_rerank: 是否启用重排序（全局开关）
        """
        self.db = db
        self.embedder = embedder
        self._reranker = reranker
        self._enable_rerank = enable_rerank and reranker is not None

    def search(
        self,
        collection_name: str,
        query: str,
        top_k: int = 5,
        where: Optional[Dict] = None,
        score_threshold: float = 0.0,
        rerank: Optional[bool] = None,
    ) -> RetrievalResult:
        """
        单集合检索

        Args:
            collection_name: 集合名称
            query: 查询文本
            top_k: 返回结果数量
            where: 元数据过滤条件
            score_threshold: 相似度阈值（0-1），低于此值的结果将被过滤
            rerank: 是否启用重排序（None=使用全局设置）

        Returns:
            RetrievalResult 实例
        """
        # 获取集合
        try:
            collection = self.db.get_collection(collection_name)
        except Exception as e:
            logger.error(f"获取集合失败: {collection_name} - {e}")
            return RetrievalResult(source_collection=collection_name)

        # 查询向量化
        query_embedding = [self.embedder.encode_query(query)]

        # 执行检索
        try:
            results = collection.query(
                query_embeddings=query_embedding,
                n_results=top_k,
                where=where,
            )
        except Exception as e:
            logger.error(f"检索失败: {e}")
            return RetrievalResult(source_collection=collection_name)

        # 解析结果
        ids = results.get("ids", [[]])[0]
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        # 将距离转换为相似度估计
        scores = [1.0 - min(d, 1.0) for d in distances]

        # 相似度过滤
        if score_threshold > 0:
            filtered = [
                (i, d, m, s)
                for i, d, m, s in zip(ids, documents, metadatas, scores)
                if s >= score_threshold
            ]
            if filtered:
                ids, documents, metadatas, scores = zip(*filtered)
                ids, documents, metadatas, scores = list(ids), list(documents), list(metadatas), list(scores)
            else:
                ids, documents, metadatas, scores = [], [], [], []

        # 重排序
        use_rerank = rerank if rerank is not None else self._enable_rerank
        if use_rerank and self._reranker is not None and documents:
            ids, documents, metadatas, scores = self._apply_rerank(
                query, ids, documents, metadatas, scores
            )

        return RetrievalResult(
            ids=ids,
            documents=documents,
            metadatas=metadatas,
            scores=scores,
            source_collection=collection_name,
        )

    def multi_search(
        self,
        collection_names: List[str],
        query: str,
        top_k_per: int = 5,
        merge_strategy: str = "score_merge",
        where: Optional[Dict] = None,
        score_threshold: float = 0.0,
    ) -> RetrievalResult:
        """
        多集合检索，从多个集合检索并合并结果

        Args:
            collection_names: 集合名称列表
            query: 查询文本
            top_k_per: 每个集合返回的结果数量
            merge_strategy: 合并策略
                - "score_merge": 按相似度分数排序合并
                - "round_robin": 轮询交替合并
            where: 元数据过滤条件
            score_threshold: 相似度阈值

        Returns:
            合并后的 RetrievalResult
        """
        all_results = []
        for col_name in collection_names:
            result = self.search(
                collection_name=col_name,
                query=query,
                top_k=top_k_per,
                where=where,
                score_threshold=score_threshold,
            )
            all_results.append(result)

        # 合并
        merged_ids = []
        merged_docs = []
        merged_metas = []
        merged_scores = []
        merged_collections = []

        if merge_strategy == "round_robin":
            # 轮询交替
            max_len = max((len(r.ids) for r in all_results), default=0)
            for i in range(max_len):
                for r in all_results:
                    if i < len(r.ids):
                        merged_ids.append(r.ids[i])
                        merged_docs.append(r.documents[i])
                        merged_metas.append(r.metadatas[i])
                        merged_scores.append(r.scores[i])
                        merged_collections.append(r.source_collection)
        else:
            # score_merge: 全部收集后按分数降序排列
            for r in all_results:
                for idx in range(len(r.ids)):
                    merged_ids.append(r.ids[idx])
                    merged_docs.append(r.documents[idx])
                    merged_metas.append(r.metadatas[idx])
                    merged_scores.append(r.scores[idx])
                    merged_collections.append(r.source_collection)

            # 按分数降序排序
            if merged_scores:
                paired = list(zip(merged_scores, merged_ids, merged_docs, merged_metas, merged_collections))
                paired.sort(key=lambda x: x[0], reverse=True)
                merged_scores, merged_ids, merged_docs, merged_metas, merged_collections = zip(*paired)
                merged_scores = list(merged_scores)
                merged_ids = list(merged_ids)
                merged_docs = list(merged_docs)
                merged_metas = list(merged_metas)
                merged_collections = list(merged_collections)

        # 去重（基于 ID）
        seen = set()
        unique_ids, unique_docs, unique_metas, unique_scores = [], [], [], []
        for i, doc_id in enumerate(merged_ids):
            if doc_id not in seen:
                seen.add(doc_id)
                unique_ids.append(doc_id)
                unique_docs.append(merged_docs[i])
                unique_metas.append(merged_metas[i])
                unique_scores.append(merged_scores[i])

        return RetrievalResult(
            ids=unique_ids,
            documents=unique_docs,
            metadatas=unique_metas,
            scores=unique_scores,
            source_collection=",".join(collection_names),
        )

    def set_reranker(self, reranker) -> None:
        """
        设置重排序模型

        Args:
            reranker: cross-encoder 重排序模型实例（预留接口）
        """
        self._reranker = reranker
        logger.info("重排序模型已设置")

    def _apply_rerank(
        self,
        query: str,
        ids: List[str],
        documents: List[str],
        metadatas: List[Dict],
        scores: List[float],
    ):
        """
        应用 Cross-Encoder 重排序

        Returns:
            重排序后的 (ids, documents, metadatas, scores)
        """
        if self._reranker is None:
            return ids, documents, metadatas, scores

        try:
            sorted_ids, sorted_docs, sorted_metas, sorted_scores = self._reranker.rerank(
                query=query,
                ids=ids,
                documents=documents,
                metadatas=metadatas,
                original_scores=scores,
            )
            return sorted_ids, sorted_docs, sorted_metas, sorted_scores
        except Exception as e:
            logger.warning(f"重排序失败，使用原始排序: {e}")
            return ids, documents, metadatas, scores
