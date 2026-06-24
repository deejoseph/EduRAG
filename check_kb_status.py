"""
检查知识库状态
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from core.db_manager import EduRAGDatabase
sys.path.insert(0, str(Path(__file__).parent / 'api'))
from config import load_config

config = load_config()
db = EduRAGDatabase(config)

# 列出所有集合
collections = db.list_collections()
print(f"所有集合: {collections}")
print()

# 检查 chinese_essays 集合
if 'chinese_essays' in collections:
    stats = db.get_collection_stats('chinese_essays')
    print(f"chinese_essays 集合统计:")
    print(f"  - 文档数量: {stats.get('document_count', 0)}")
    print(f"  - 其他信息: {stats}")
else:
    print("❌ chinese_essays 集合不存在")

print("\n" + "="*60)
print("提示: 如果文档数量没有增加，可能的原因:")
print("1. 使用了不同的 collection 名称")
print("2. 数据写入了但未被正确统计")
print("3. 需要重启后端服务刷新缓存")
