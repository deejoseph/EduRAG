"""API 接口测试脚本"""
import requests
import json

BASE = "http://127.0.0.1:5000"

print("=" * 55)
print("  EduRAG API 接口测试")
print("=" * 55)

# 1. 健康检查
print("\n[1] GET /health")
r = requests.get(f"{BASE}/health")
print(f"    {r.status_code} -> {r.json()}")

# 2. 知识库统计
print("\n[2] GET /search/stats")
r = requests.get(f"{BASE}/search/stats")
d = r.json()
print(f"    {r.status_code} -> 集合数: {d['total_collections']}, 文档数: {d['total_documents']}")
print(f"    LLM: {d['llm_model']}, Embedding: {d['embedding_model']}")

# 3. 纯检索（不经过 LLM，速度快）
print("\n[3] POST /search/query（纯检索）")
r = requests.post(f"{BASE}/search/query", json={
    "query": "记叙文开头技巧",
    "top_k": 3,
    "with_llm": False,
})
d = r.json()
print(f"    {r.status_code} -> 检索到 {d['count']} 条")
for i, item in enumerate(d['results'], 1):
    print(f"    [{i}] score={item['score']:.4f} | {item['metadata'].get('title', '')}")

# 4. 审题分析（RAG，含 LLM）
print("\n[4] POST /writing/analyze（审题分析，含 LLM，需等待）...")
r = requests.post(f"{BASE}/writing/analyze", json={
    "topic": "每个人都要学习与他人相处，但有时我们也需要与自己相处",
    "topic_type": "材料",
    "grade_level": "高中",
    "top_k": 5,
})
d = r.json()
print(f"    {r.status_code} -> 引用 {d['ref_count']} 条资料")
print(f"    回答前200字：{d['answer'][:200]}...")

# 5. 作文评估（RAG）
print("\n[5] POST /writing/evaluate（作文评估，含 LLM）...")
r = requests.post(f"{BASE}/writing/evaluate", json={
    "essay": "成长的滋味\n\n成长是每个人都要经历的过程。记得初二那年数学成绩不好，老师每天帮我讲题，期末考了85分，我终于明白了成长的意义。",
    "topic": "成长的滋味",
    "grade_level": "初中",
    "top_k": 5,
})
d = r.json()
print(f"    {r.status_code} -> 引用 {d['ref_count']} 条资料")
print(f"    回答前200字：{d['answer'][:200]}...")

# 6. 列出集合
print("\n[6] GET /search/collections")
r = requests.get(f"{BASE}/search/collections")
d = r.json()
for c in d['collections']:
    print(f"    集合: {c['name']} ({c['count']} 条)")

print("\n" + "=" * 55)
print("  全部测试完成")
print("=" * 55)
