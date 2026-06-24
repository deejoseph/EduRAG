"""
检查 chinese_essays 集合中的文档类型分布
"""

import chromadb

# 连接到ChromaDB
client = chromadb.PersistentClient(path="./data/chroma_db")
collection = client.get_collection('chinese_essays')

print(f"总文档数: {collection.count()}")
print("\n正在分析文档类型...")

# 获取大量样本进行分析
sample_size = min(1000, collection.count())
sample = collection.peek(limit=sample_size)

# 统计元数据中的分类
category_count = {}
year_count = {}

for i in range(sample_size):
    meta = sample['metadatas'][i] if 'metadatas' in sample else {}
    
    # 统计类别
    category = meta.get('doc_category', meta.get('category', 'Unknown'))
    category_count[category] = category_count.get(category, 0) + 1
    
    # 统计年份（如果有）
    year = meta.get('year', None)
    if year:
        year_count[str(year)] = year_count.get(str(year), 0) + 1

print(f"\n采样 {sample_size} 个文档的统计结果:")
print(f"\n按类别分布:")
for cat, count in sorted(category_count.items(), key=lambda x: x[1], reverse=True)[:10]:
    print(f"  {cat}: {count}")

print(f"\n按年份分布:")
for year, count in sorted(year_count.items(), reverse=True)[:10]:
    print(f"  {year}: {count}")

# 检查是否有2026年的文档
if '2026' in year_count:
    print(f"\n✅ 找到 {year_count['2026']} 个2026年的文档")
else:
    print(f"\n❌ 没有找到2026年的文档")
