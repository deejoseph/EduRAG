"""
简化版高考作文采集脚本 - 先采集2026年数据
"""

import requests
from bs4 import BeautifulSoup
import json
import os
import time
from pathlib import Path

# 配置
BASE_URL = "https://gaokao.eol.cn"
OUTPUT_DIR = Path("data/gaokao_essays")
PDF_DIR = OUTPUT_DIR / "pdfs"
JSON_FILE = OUTPUT_DIR / "gaokao_essays_2026.json"

# 创建目录
PDF_DIR.mkdir(parents=True, exist_ok=True)

# HTTP会话
session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
})


def fetch_page(url):
    """获取页面内容"""
    try:
        print(f"GET {url[:80]}...")
        response = session.get(url, timeout=30)
        response.encoding = 'utf-8'
        return response.text
    except Exception as e:
        print(f"ERROR: {e}")
        return None


def main():
    print("=" * 60)
    print("开始采集2026年高考作文...")
    print("=" * 60)
    
    # 已知的2026年作文链接（从浏览器代理获取）
    essays_2026 = [
        {
            'region': '全国I卷',
            'title': '对词语理解的变化',
            'url': 'https://gaokao.eol.cn/zuowen/jiqiao/202606/t20260607_2741913.shtml'
        },
        {
            'region': '全国II卷',
            'title': '关于"体"与"源"的联想与思考',
            'url': 'https://gaokao.eol.cn/zuowen/jiqiao/202606/t20260607_2741916.shtml'
        },
        {
            'region': '北京卷',
            'title': '做规划与下功夫',
            'url': 'https://gaokao.eol.cn/bei_jing/dongtai/202606/t20260607_2741918.shtml'
        },
        {
            'region': '天津卷',
            'title': '"调"',
            'url': 'https://gaokao.eol.cn/tian_jin/dongtai/202606/t20260607_2741923.shtml'
        },
        {
            'region': '上海卷',
            'title': '对科技改造世界的认识和思考',
            'url': 'https://gaokao.eol.cn/shang_hai/dongtai/202606/t20260607_2741930.shtml'
        }
    ]
    
    all_essays = []
    
    for i, essay_info in enumerate(essays_2026, 1):
        print(f"\n[{i}/{len(essays_2026)}] 处理: {essay_info['region']}")
        
        # 获取页面
        html = fetch_page(essay_info['url'])
        if not html:
            continue
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # 提取内容
        content_div = soup.find('div', class_=re.compile(r'content|article'))
        content = content_div.get_text(separator='\n', strip=True) if content_div else ""
        
        # 保存HTML文件
        safe_region = re.sub(r'[^\w]', '_', essay_info['region'])
        safe_title = re.sub(r'[^\w]', '_', essay_info['title'])[:30]
        filename = f"2026_{safe_region}_{safe_title}"
        html_file = PDF_DIR / f"{filename}.html"
        
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html)
        
        print(f"SAVED: {html_file.name}")
        
        # 记录数据
        essay_record = {
            'year': '2026',
            'region': essay_info['region'],
            'title': essay_info['title'],
            'url': essay_info['url'],
            'content': content[:500],  # 只保存前500字符作为预览
            'html_path': str(html_file),
            'is_sample': False,
            'tags': ['高考']
        }
        all_essays.append(essay_record)
        
        time.sleep(1)
    
    # 保存JSON
    with open(JSON_FILE, 'w', encoding='utf-8') as f:
        json.dump(all_essays, f, ensure_ascii=False, indent=2)
    
    print(f"\nDONE! 共采集 {len(all_essays)} 篇作文")
    print(f"HTML files: {PDF_DIR.absolute()}")
    print(f"JSON data: {JSON_FILE.absolute()}")


if __name__ == '__main__':
    import re
    main()
