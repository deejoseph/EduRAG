"""
检查最近导入的文档
"""

import chromadb
from datetime import datetime

# 连接到ChromaDB
client = chromadb.PersistentClient(path="./data/chroma_db")
collection = client.get_collection('chinese_essays')

# 获取所有包含"2026"或"高考"的文档
print("查找包含'2026'或'高考'的文档...")

# 先随机采样一些文档看看ID格式
sample = collection.peek(limit=10)
print("\n最近的10个文档ID:")
for i, doc_id in enumerate(sample['ids']):
    meta = sample['metadatas'][i] if 'metadatas' in sample else {}
    print(f"  {doc_id}")

# 尝试搜索包含特定关键词的文档
try:
    results = collection.query(
        query_texts=["2026年高考"],
        n_results=5
    )
    
    print(f"\n搜索'2026年高考'的结果 ({len(results['ids'][0])} 条):")
    for i, doc_id in enumerate(results['ids'][0]):
        doc_text = results['documents'][0][i][:100] if 'documents' in results else ''
        meta = results['metadatas'][0][i] if 'metadatas' in results else {}
        print(f"  ID: {doc_id}")
        print(f"  Meta: {meta}")
        print(f"  Text: {doc_text[:80]}...")
        print()
except Exception as e:
    print(f"搜索失败: {e}")

print(f"\n总文档数: {collection.count()}")
