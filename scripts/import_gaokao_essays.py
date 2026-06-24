"""
高考作文导入脚本 - 简化版
直接调用现有的 import_docs.py 来导入HTML文件到知识库
"""

import json
from pathlib import Path
import sys
import subprocess

def main():
    print("="*60)
    print("高考作文导入工具 - 简化版")
    print("="*60)
    
    # 查找JSON文件
    json_files = list(Path("data/gaokao_essays").glob("gaokao_essays_*.json"))
    
    if not json_files:
        print("❌ 未找到高考作文JSON文件")
        print("请先运行 collect_gaokao_simple.py 采集数据")
        return
    
    # 使用最新的JSON文件
    json_file = sorted(json_files)[-1]
    print(f"DATA FILE: {json_file}")
    
    # 加载数据
    with open(json_file, 'r', encoding='utf-8') as f:
        essays = json.load(f)
    
    print(f"Loaded {len(essays)} essays")
    
    # 统计信息
    by_year = {}
    by_region = {}
    
    for essay in essays:
        if essay.get('is_sample'):
            continue
        
        year = essay['year']
        region = essay['region']
        
        by_year[year] = by_year.get(year, 0) + 1
        by_region[region] = by_region.get(region, 0) + 1
    
    print("\n按年份统计:")
    for year in sorted(by_year.keys()):
        print(f"  {year}年: {by_year[year]} 篇")
    
    print("\n按地区统计:")
    for region in sorted(by_region.keys()):
        print(f"  {region}: {by_region[region]} 篇")
    
    # 检查HTML文件
    html_dir = Path("data/gaokao_essays/pdfs")
    html_files = list(html_dir.glob("*.html"))
    
    print(f"\nHTML files: {len(html_files)}")
    print(f"   Location: {html_dir.absolute()}")
    
    print("\n" + "="*60)
    print("下一步操作:")
    print("="*60)
    print("\n1. 将HTML文件转换为TXT格式（便于导入）")
    print("2. 使用 import_docs.py 导入到知识库")
    print("3. 手动添加题目到题库（带'高考'标签）")
    
    # 创建转换后的TXT文件目录
    txt_dir = Path("data/gaokao_essays/txts")
    txt_dir.mkdir(exist_ok=True)
    
    print(f"\nConverting HTML to TXT...")
    
    from bs4 import BeautifulSoup
    
    converted = 0
    for html_file in html_files:
        try:
            with open(html_file, 'r', encoding='utf-8') as f:
                html = f.read()
            
            soup = BeautifulSoup(html, 'html.parser')
            
            # 提取正文
            content_div = soup.find('div', class_='article') or soup.find('div', class_='content')
            if content_div:
                text = content_div.get_text(separator='\n', strip=True)
            else:
                # fallback: 提取所有段落
                paragraphs = soup.find_all('p')
                text = '\n\n'.join([p.get_text(strip=True) for p in paragraphs])
            
            # 保存为TXT
            txt_file = txt_dir / html_file.with_suffix('.txt').name
            with open(txt_file, 'w', encoding='utf-8') as f:
                f.write(text)
            
            converted += 1
            
        except Exception as e:
            print(f"  ❌ 转换失败 {html_file.name}: {e}")
    
    print(f"OK Converted {converted} files")
    print(f"TXT dir: {txt_dir.absolute()}")
    
    print("\n" + "="*60)
    print("现在可以运行以下命令导入知识库:")
    print("="*60)
    print(f"\npython scripts/import_docs.py --dir data/gaokao_essays/txts --collection chinese_essays")


if __name__ == '__main__':
    main()
