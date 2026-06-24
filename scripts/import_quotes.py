"""
名人名言导入脚本
将 data/quotes 目录中的名言诗词导入到独立的 quotes_collection 知识库
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from docx import Document
import chromadb
import re
import json
from datetime import datetime

def extract_quotes_from_docx(docx_path):
    """从DOCX文件中提取名人名言"""
    try:
        doc = Document(str(docx_path))
        paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
        
        quotes = []
        current_author = None
        current_category = None
        
        for para in paragraphs:
            # 跳过空行和标题
            if len(para) < 5:
                continue
            
            # 检测分类标题（如"一、爱国类"）
            category_match = re.match(r'^[一二三四五六七八九十]+、(.+)$', para)
            if category_match and len(para) < 20:
                current_category = category_match.group(1)
                continue
            
            # 检测作者（如"——李白"或"—鲁迅"）
            author_match = re.search(r'[—-]\s*([^\s。！？]{2,10})$', para)
            if author_match:
                current_author = author_match.group(1)
            
            # 提取名言（包含作者信息）
            if len(para) > 10 and '。' in para or '！' in para or '？' in para:
                quote_text = para
                
                # 如果没有检测到作者，尝试从文本中提取
                if not current_author:
                    # 查找常见的作者标记
                    author_patterns = [
                        r'[—-]\s*([^\s。！？]{2,10})$',
                        r'《([^》]+)》',
                        r'\(([^\)]+)\)',
                    ]
                    for pattern in author_patterns:
                        match = re.search(pattern, para)
                        if match:
                            current_author = match.group(1)
                            break
                
                quotes.append({
                    'text': quote_text,
                    'author': current_author or '未知',
                    'category': current_category or '其他',
                    'source_file': docx_path.name,
                    'created_at': datetime.now().isoformat()
                })
        
        return quotes
    
    except Exception as e:
        print(f"处理文件 {docx_path.name} 时出错: {e}")
        return []


def import_quotes_to_chromadb(quotes, collection_name="quotes_collection"):
    """将名言导入ChromaDB"""
    
    # 连接ChromaDB
    client = chromadb.PersistentClient(path="./data/chroma_db")
    
    # 删除已存在的集合（如果需要重建）
    existing_collections = [col.name for col in client.list_collections()]
    if collection_name in existing_collections:
        print(f"删除已存在的集合: {collection_name}")
        client.delete_collection(collection_name)
    
    # 创建新集合
    collection = client.create_collection(
        name=collection_name,
        metadata={"description": "名人名言和诗词收藏"}
    )
    
    print(f"创建集合: {collection_name}")
    
    # 准备数据
    documents = []
    metadatas = []
    ids = []
    
    for i, quote in enumerate(quotes):
        doc_id = f"quote_{i:04d}"
        documents.append(quote['text'])
        metadatas.append({
            'author': quote['author'],
            'category': quote['category'],
            'source_file': quote['source_file'],
            'created_at': quote['created_at']
        })
        ids.append(doc_id)
    
    # 添加到ChromaDB（需要embedding）
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer('BAAI/bge-base-zh-v1.5')
    
    print(f"正在为 {len(documents)} 条名言生成向量...")
    embeddings = model.encode(documents, show_progress_bar=True)
    
    collection.add(
        ids=ids,
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas
    )
    
    print(f"OK Imported {len(documents)} quotes to '{collection_name}'")
    return len(documents)


def save_quotes_json(quotes, output_file="data/quotes/all_quotes.json"):
    """保存名言为JSON文件（备用）"""
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(quotes, f, ensure_ascii=False, indent=2)
    
    print(f"JSON saved to: {output_path}")


def main():
    print("=" * 60)
    print("名人名言导入工具")
    print("=" * 60)
    
    # 扫描DOCX文件
    quotes_dir = Path("data/quotes")
    docx_files = list(quotes_dir.glob("*.docx"))
    
    if not docx_files:
        print("❌ 未找到DOCX文件")
        return
    
    print(f"FOUND {len(docx_files)} DOCX files\n")
    
    # 提取所有名言
    all_quotes = []
    for docx_file in docx_files:
        print(f"处理: {docx_file.name}")
        quotes = extract_quotes_from_docx(docx_file)
        print(f"  提取 {len(quotes)} 条名言")
        all_quotes.extend(quotes)
    
    print(f"\n总计提取 {len(all_quotes)} 条名言")
    
    # 保存到JSON
    save_quotes_json(all_quotes)
    
    # 导入到ChromaDB
    print("\n开始导入到ChromaDB...")
    count = import_quotes_to_chromadb(all_quotes)
    
    print("\n" + "=" * 60)
    print(f"DONE! Total {count} quotes imported")
    print("=" * 60)
    
    # 统计信息
    by_category = {}
    by_author = {}
    for quote in all_quotes:
        cat = quote['category']
        author = quote['author']
        by_category[cat] = by_category.get(cat, 0) + 1
        by_author[author] = by_author.get(author, 0) + 1
    
    print("\n按分类统计:")
    for cat, count in sorted(by_category.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"  {cat}: {count}")
    
    print("\n按作者统计 (前10):")
    for author, count in sorted(by_author.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"  {author}: {count}")


if __name__ == '__main__':
    main()
