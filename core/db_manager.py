"""
EduRAG 数据库管理模块
封装 ChromaDB 操作，提供统一的向量存储和检索接口
"""

import os
import logging
from typing import List, Dict, Any, Optional

import chromadb
from chromadb.config import Settings

from core.embedding import EmbeddingModel

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EduRAGDatabase:
    """EduRAG 向量数据库管理器"""
    
    def __init__(
        self, 
        db_path: str = "./data/chroma_db",
        embedding_model: str = "BAAI/bge-base-zh-v1.5",
        device: str = None,
        embedder: Optional[EmbeddingModel] = None
    ):
        self.db_path = db_path
        self.embedding_model_name = embedding_model
        
        # 确保目录存在
        os.makedirs(db_path, exist_ok=True)
        
        # 初始化 ChromaDB 客户端（持久化模式）
        self.client = chromadb.PersistentClient(
            path=db_path,
            settings=Settings(anonymized_telemetry=False)
        )
        logger.info(f"ChromaDB 客户端初始化成功，路径: {db_path}")
        
        # 使用外部注入的 embedder 或自行创建
        if embedder is not None:
            self.embedder = embedder
        else:
            self.embedder = EmbeddingModel(model_name=embedding_model, device=device)
        logger.info(f"Embedding 模型就绪: {self.embedder.model_name} (device: {self.embedder.device})")
        
        # 缓存已打开的集合
        self._collections_cache = {}
    
    def create_collection(
        self, 
        name: str, 
        metadata: Optional[Dict] = None,
        force_recreate: bool = False
    ):
        """创建或获取集合，metadata 不能为空字典"""
        if force_recreate and self.collection_exists(name):
            self.client.delete_collection(name)
            logger.info(f"已删除旧集合: {name}")

        try:
            # ChromaDB 要求 metadata 不能是空字典，所以如果是空或不传则使用 None
            if metadata is None or metadata == {}:
                collection = self.client.get_or_create_collection(name=name)
            else:
                collection = self.client.get_or_create_collection(name=name, metadata=metadata)
            self._collections_cache[name] = collection
            logger.info(f"集合准备就绪: {name}")
            return collection
        except Exception as e:
            logger.error(f"创建/获取集合失败 {name}: {e}")
            raise
    
    def collection_exists(self, name: str) -> bool:
        try:
            self.client.get_collection(name)
            return True
        except (ValueError, chromadb.errors.NotFoundError):
            return False
    
    def list_collections(self) -> List[str]:
        """列出所有集合名称"""
        return [col.name for col in self.client.list_collections()]
    
    def get_collection(self, name: str):
        """获取已存在的集合"""
        if name in self._collections_cache:
            return self._collections_cache[name]
        
        collection = self.client.get_collection(name)
        self._collections_cache[name] = collection
        return collection
    
    def add_documents(
        self,
        collection_name: str,
        documents: List[str],
        metadatas: Optional[List[Dict]] = None,
        ids: Optional[List[str]] = None
    ) -> List[str]:
        """
        向集合中添加文档
        
        Args:
            collection_name: 集合名称
            documents: 文档内容列表
            metadatas: 元数据列表，每条对应一个文档
            ids: 自定义 ID 列表，不提供则自动生成
            
        Returns:
            添加的文档 ID 列表
        """
        if not documents:
            logger.warning("没有文档需要添加")
            return []
        
        collection = self.get_collection(collection_name)
        
        # 生成 Embedding 向量
        logger.info(f"正在为 {len(documents)} 条文档生成向量...")
        embeddings = self.embedder.encode(documents, show_progress_bar=True)
        
        # 生成 ID（如果未提供）
        if ids is None:
            # 获取当前集合中的文档数量，用于生成不重复 ID
            try:
                existing_count = collection.count()
            except:
                existing_count = 0
            ids = [f"{collection_name}_{existing_count + i}" for i in range(len(documents))]
        
        # 处理元数据（确保每条文档都有）
        if metadatas is None:
            metadatas = [{} for _ in documents]
        elif len(metadatas) != len(documents):
            raise ValueError(f"metadatas 长度 ({len(metadatas)}) 与 documents 长度 ({len(documents)}) 不匹配")
        
        # 添加到 ChromaDB
        try:
            collection.add(
                ids=ids,
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas
            )
            logger.info(f"成功添加 {len(documents)} 条文档到集合 '{collection_name}'")
            return ids
        except Exception as e:
            logger.error(f"添加文档失败: {e}")
            raise
    
    def search(
        self,
        collection_name: str,
        query: str,
        top_k: int = 5,
        where: Optional[Dict] = None,
        score_threshold: float = 0.0
    ) -> Dict[str, Any]:
        """
        检索与查询最相似的文档
        
        Args:
            collection_name: 集合名称
            query: 查询文本
            top_k: 返回结果数量
            where: 元数据过滤条件，如 {"grade": "9"}
            score_threshold: 相似度阈值（0-1），低于此值的结果将被过滤
            
        Returns:
            检索结果字典，包含 ids, documents, metadatas, distances
        """
        collection = self.get_collection(collection_name)
        
        # 查询向量化
        query_embedding = [self.embedder.encode_query(query)]
        
        # 执行检索
        try:
            results = collection.query(
                query_embeddings=query_embedding,
                n_results=top_k,
                where=where
            )
        except Exception as e:
            logger.error(f"检索失败: {e}")
            return {"ids": [[]], "documents": [[]], "metadatas": [[]], "distances": [[]]}
        
        # 相似度过滤（Chromadb 返回的是 L2 距离，需要转换）
        # 对于余弦相似度，距离 ≈ 1 - 相似度，此处简单过滤
        if score_threshold > 0 and results['distances'] and results['distances'][0]:
            filtered_ids = []
            filtered_docs = []
            filtered_metadatas = []
            filtered_distances = []
            
            for i, dist in enumerate(results['distances'][0]):
                # 将距离转换为相似度估计（粗略）
                similarity = 1 - min(dist, 1.0)
                if similarity >= score_threshold:
                    filtered_ids.append(results['ids'][0][i])
                    filtered_docs.append(results['documents'][0][i])
                    filtered_metadatas.append(results['metadatas'][0][i])
                    filtered_distances.append(dist)
            
            results['ids'][0] = filtered_ids
            results['documents'][0] = filtered_docs
            results['metadatas'][0] = filtered_metadatas
            results['distances'][0] = filtered_distances
        
        return results
    
    def delete_collection(self, name: str) -> bool:
        """删除整个集合"""
        try:
            self.client.delete_collection(name)
            if name in self._collections_cache:
                del self._collections_cache[name]
            logger.info(f"已删除集合: {name}")
            return True
        except Exception as e:
            logger.error(f"删除集合失败 {name}: {e}")
            return False
    
    def delete_documents(self, collection_name: str, ids: List[str]) -> bool:
        """从集合中删除指定 ID 的文档"""
        try:
            collection = self.get_collection(collection_name)
            collection.delete(ids=ids)
            logger.info(f"从 {collection_name} 删除 {len(ids)} 条文档")
            return True
        except Exception as e:
            logger.error(f"删除文档失败: {e}")
            return False
    
    def get_collection_count(self, collection_name: str) -> int:
        """获取集合中的文档数量"""
        try:
            collection = self.get_collection(collection_name)
            return collection.count()
        except:
            return 0
    
    def clear_all(self):
        """清空所有数据（危险操作）"""
        confirm = input("确认清空所有数据？输入 'yes' 继续: ")
        if confirm.lower() == 'yes':
            for name in self.list_collections():
                self.delete_collection(name)
            logger.info("已清空所有数据")
        else:
            logger.info("操作取消")


# 简单测试（直接运行此文件时）
if __name__ == "__main__":
    # 测试数据库功能
    db = EduRAGDatabase(db_path="./test_db")
    
    # 创建测试集合
    db.create_collection("test_essays", metadata={"subject": "chinese"})
    
    # 添加测试文档
    docs = [
        "母爱是清晨的一杯热牛奶，是深夜的一盏守候的灯。",
        "成长是一场蜕变，从幼稚到成熟。",
        "友谊是人生路上的明灯。"
    ]
    metas = [
        {"grade": "7", "topic": "母爱"},
        {"grade": "8", "topic": "成长"},
        {"grade": "9", "topic": "友谊"}
    ]
    db.add_documents("test_essays", docs, metas)
    
    # 检索测试
    results = db.search("test_essays", "怎么写关于母爱的作文", top_k=2)
    print("\n检索结果：")
    for i, doc in enumerate(results['documents'][0]):
        print(f"{i+1}. {doc}")
    
    # 清理测试
    db.delete_collection("test_essays")
    print(f"\n测试完成，剩余集合: {db.list_collections()}")