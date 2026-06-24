"""
将239条高考作文题目批量添加到题库（favorites）
"""

import requests
import json
from pathlib import Path

# 加载完整JSON数据
json_file = Path("data/gaokao_essays/all_gaokao_topics_complete.json")
with open(json_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f"Loaded {data['total_years']} years, {data['total_essays']} essays from {json_file}")

added = 0
skipped = 0
failed = 0

# 遍历所有年份和作文
for year_data in data['years']:
    year = year_data['year']
    
    for essay in year_data['essays']:
        title = essay['title']
        region = essay['region']
        url = essay['url']
        
        # 跳过没有标题或标题太短的
        if not title or len(title.strip()) < 2:
            continue
        
        # 构建作文提示词
        essay_prompt = f"{year}年{region}高考作文题目：{title}"
        
        try:
            # 检查是否已存在
            resp = requests.get('http://localhost:5000/hot-topics/favorites?sort_by=favorited_at')
            existing_titles = [t.get('title') for t in resp.json().get('topics', [])]
            
            if title in existing_titles:
                print(f"SKIP: [{year}] {title[:40]}")
                skipped += 1
                continue
            
            # 添加到题库（注意：需要嵌套在 topic 字段中）
            topic_data = {
                'topic': {
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
            
            resp = requests.post('http://localhost:5000/hot-topics/favorite', json=topic_data)
            
            if resp.status_code == 200:
                print(f"OK: [{year}-{region}] {title[:50]}")
                added += 1
            else:
                print(f"FAIL: {resp.status_code} - {resp.text[:100]}")
                failed += 1
                
        except Exception as e:
            print(f"ERROR: {e}")
            failed += 1

print(f"\n{'='*60}")
print(f"Done!")
print(f"  Added: {added}")
print(f"  Skipped: {skipped}")
print(f"  Failed: {failed}")
print(f"{'='*60}")
