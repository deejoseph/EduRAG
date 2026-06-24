"""
检查名人名言文件内容
"""

from pathlib import Path
from docx import Document

quotes_dir = Path("data/quotes")
docx_files = list(quotes_dir.glob("*.docx"))

print(f"找到 {len(docx_files)} 个DOCX文件:\n")

for docx_file in docx_files:
    print(f"文件: {docx_file.name}")
    try:
        doc = Document(str(docx_file))
        paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
        print(f"  段落数: {len(paragraphs)}")
        print(f"  前10段内容:")
        for i, para in enumerate(paragraphs[:10], 1):
            print(f"    {i}. {para[:80]}...")
        print()
    except Exception as e:
        print(f"  错误: {e}\n")
