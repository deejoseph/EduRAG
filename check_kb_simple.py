"""
检查知识库状态 - 简化版
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import chromadb

# 连接到ChromaDB
client = chromadb.PersistentClient(path="./data/chroma_db")

# 列出所有集合
collections = client.list_collections()
print(f"所有集合 ({len(collections)} 个):")
for col in collections:
    print(f"  - {col.name}")
print()

# 检查 chinese_essays 集合
if any(col.name == 'chinese_essays' for col in collections):
    collection = client.get_collection('chinese_essays')
    count = collection.count()
    print(f"chinese_essays 集合:")
    print(f"  - 文档数量: {count}")
    
    # 获取一些样本查看元数据
    if count > 0:
        sample = collection.peek(limit=3)
        print(f"\n  样本数据 (前3条):")
        for i, doc_id in enumerate(sample['ids']):
            meta = sample['metadatas'][i] if 'metadatas' in sample else {}
            title = meta.get('title', 'N/A')[:50] if meta else 'N/A'
            print(f"    [{i+1}] ID: {doc_id[:20]}... | Title: {title}")
else:
    print("❌ chinese_essays 集合不存在")

print("\n" + "="*60)
print("如果文档数量不是预期的，可能原因:")
print("1. 之前导入的数据已被删除或覆盖")
print("2. 使用了不同的数据库路径")
print("3. 需要重启后端服务以刷新缓存")
