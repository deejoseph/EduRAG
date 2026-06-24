import requests
import json

print("=" * 60)
print("测试 API 返回数据")
print("=" * 60)

# 调用 favorites API
try:
    response = requests.get('http://localhost:5000/hot-topics/favorites?sort_by=favorited_at')
    print(f"\n✅ API 调用成功，状态码: {response.status_code}")
    
    data = response.json()
    print(f"📊 返回题目数: {data.get('total', 0)}")
    
    if data.get('topics'):
        first = data['topics'][0]
        print(f"\n第一个题目的字段:")
        print(f"  title: {first.get('title', '')[:50]}...")
        print(f"  guided_practice_count: {first.get('guided_practice_count', 'N/A')}")
        print(f"  intensive_practice_count: {first.get('intensive_practice_count', 'N/A')}")
        print(f"  practice_count: {first.get('practice_count', 'N/A')}")
        
        # 检查是否有引导练习记录的题目
        guided_topics = [t for t in data['topics'] if t.get('guided_practice_count', 0) > 0]
        print(f"\n📝 有引导练习记录的主题数: {len(guided_topics)}")
        if guided_topics:
            for t in guided_topics[:3]:
                print(f"  - {t['title'][:50]}... : {t['guided_practice_count']}次")
    
except Exception as e:
    print(f"\n❌ API 调用失败: {e}")

print("\n" + "=" * 60)
