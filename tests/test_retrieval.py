"""
EduRAG 知识库检索测试脚本
测试导入后的 ChromaDB 数据质量和检索效果
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import logging
from core.embedding import EmbeddingModel
from core.db_manager import EduRAGDatabase
from core.retriever import Retriever

logging.basicConfig(level=logging.WARNING)


def test_retrieval():
    """检索效果测试"""
    print("=" * 60)
    print("  EduRAG 知识库检索测试")
    print("=" * 60)

    # 初始化
    embedder = EmbeddingModel()
    db = EduRAGDatabase(db_path="./data/chroma_db", embedder=embedder)
    retriever = Retriever(db=db, embedder=embedder)

    collection_name = "chinese_essays"

    # 1. 集合基本信息
    count = db.get_collection_count(collection_name)
    collections = db.list_collections()
    print(f"\n[集合信息]")
    print(f"  现有集合: {collections}")
    print(f"  {collection_name} 文档数: {count}")

    # 2. 测试查询列表
    test_queries = [
        {
            "query": "高考作文如何写好开头？",
            "desc": "写作技巧类",
        },
        {
            "query": "以「成长」为主题的满分作文有哪些好的素材？",
            "desc": "范文素材类",
        },
        {
            "query": "2023年全国卷高考作文题目是什么？",
            "desc": "真题信息类",
        },
        {
            "query": "议论文如何做到论点鲜明、论据充分？",
            "desc": "写作方法类",
        },
        {
            "query": "关于家国情怀的作文素材和名言警句",
            "desc": "素材积累类",
        },
    ]

    # 3. 逐个测试
    for i, tq in enumerate(test_queries, 1):
        print(f"\n{'─'*60}")
        print(f"测试 {i}: [{tq['desc']}]")
        print(f"  查询: {tq['query']}")
        print()

        result = retriever.search(
            collection_name=collection_name,
            query=tq["query"],
            top_k=3,
        )

        if not result.documents:
            print("  ❌ 未检索到结果")
            continue

        for j, (doc, meta, score) in enumerate(
            zip(result.documents, result.metadatas, result.scores), 1
        ):
            source = meta.get("source_file", "未知")
            category = meta.get("doc_category", "未知")
            title = meta.get("title", "")
            year = meta.get("year", "")
            # 截取前 120 字展示
            preview = doc[:120].replace("\n", " ") + ("..." if len(doc) > 120 else "")
            print(f"  [{j}] 相似度: {score:.3f} | {category} | {title}")
            print(f"      来源: {source}")
            if year:
                print(f"      年份: {year}")
            print(f"      内容: {preview}")
            print()

    print(f"{'─'*60}")
    print("\n测试完成！")


if __name__ == "__main__":
    test_retrieval()
