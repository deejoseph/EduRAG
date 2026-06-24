"""
将高考作文题目添加到题库（favorites）
"""

import requests
import json
from pathlib import Path

# 加载JSON数据
json_file = Path("data/gaokao_essays/gaokao_essays_2026.json")
with open(json_file, 'r', encoding='utf-8') as f:
    essays = json.load(f)

print(f"Loaded {len(essays)} essays from {json_file}")

# 只处理作文题目（非范文）
topics = [e for e in essays if not e.get('is_sample')]
print(f"Found {len(topics)} essay topics (excluding samples)")

added = 0
skipped = 0

for essay in topics:
    title = essay['title']
    region = essay['region']
    year = essay['year']
    
    # 构建作文提示词
    essay_prompt = f"{year}年{region}高考作文题目：{title}"
    
    # 检查是否已存在
    try:
        resp = requests.get('http://localhost:5000/hot-topics/favorites?sort_by=favorited_at')
        existing_titles = [t.get('title') for t in resp.json().get('topics', [])]
        
        if title in existing_titles:
            print(f"SKIP: {title[:40]}")
            skipped += 1
            continue
        
        # 添加到题库（注意：需要嵌套在 topic 字段中）
        data = {
            'topic': {  # 关键：嵌套在 topic 字段中
                'title': title,
                'essay_prompt': essay_prompt,
                'category': '高考作文',
                'difficulty': '中等',
                'year': year,
                'region': region,
                'tags': ['高考'],
                'source': 'gaokao.eol.cn'
            }
        }
        
        resp = requests.post('http://localhost:5000/hot-topics/favorite', json=data)
        
        if resp.status_code == 200:
            print(f"OK: {title[:50]}")
            added += 1
        else:
            print(f"FAIL: {resp.status_code} - {resp.text[:100]}")
            
    except Exception as e:
        print(f"ERROR: {e}")

print(f"\nDone! Added: {added}, Skipped: {skipped}")
