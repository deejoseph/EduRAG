"""
清空 chinese_essays 集合并重新导入
"""

import chromadb
import sys
from pathlib import Path

# 连接到ChromaDB
client = chromadb.PersistentClient(path="./data/chroma_db")

# 列出所有集合
collections = client.list_collections()
print(f"当前集合: {[col.name for col in collections]}")

# 删除 chinese_essays 集合
if any(col.name == 'chinese_essays' for col in collections):
    print("\n正在删除 chinese_essays 集合...")
    client.delete_collection('chinese_essays')
    print("OK Deleted")
else:
    print("\nNOT FOUND")

print("\n现在可以重新运行导入命令:")
print("cd d:\\PixelSmile\\EduRAG")
print("C:\\Users\\deejo\\anaconda3\\envs\\pixel_ai\\python.exe scripts/import_docs.py --source data/gaokao_essays/docx --collection chinese_essays --file-types docx --force")
