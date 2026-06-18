import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.db_manager import EduRAGDatabase
from core.llm_client import OllamaClient
from core.rag_pipeline import RAGPipeline

db = EduRAGDatabase()
llm = OllamaClient(model="qwen2.5:7b")
rag = RAGPipeline(db, llm, default_collection="chinese_essays",
                  default_score_threshold=0.25, default_top_k=8)

print("=" * 60)
print("  EduRAG 端到端 RAG 测试（调参版）")
print("  阈值: 0.25 | top_k: 8")
print("=" * 60)

# 测试 1：记叙文写作指导
print("\n[测试 1] 记叙文开头技巧")
result = rag.query(
    question="请介绍记叙文（叙事类文章）开头的几种常见写法和技巧，"
             "如开门见山、倒叙、设置悬念等，并结合具体例子说明每种写法的效果。",
    role="高中语文写作教学专家",
    expertise="记叙文写作技巧、叙事结构设计、文学性表达",
    score_threshold=0.25,
    top_k=8,
    temperature=0.7,
)
print(f"\n回答：\n{result['answer']}")
print(f"\n检索到 {len(result['retrieved_docs'])} 条参考资料")
for i, (doc, meta) in enumerate(zip(result['retrieved_docs'], result['metadatas']), 1):
    print(f"  [{i}] {meta.get('title', '')} ({meta.get('doc_category', '')})")

# 测试 2：高考作文审题
print("\n" + "─" * 60)
print("\n[测试 2] 高考作文审题分析")
result2 = rag.query(
    question="2023年高考语文全国卷的作文题目有哪些？请分析其中一个题目的审题要点和立意方向。",
    role="高考语文备考指导教师",
    expertise="高考作文命题分析、审题立意、评分标准解读",
    score_threshold=0.25,
    top_k=8,
    temperature=0.5,
)
print(f"\n回答：\n{result2['answer']}")
print(f"\n检索到 {len(result2['retrieved_docs'])} 条参考资料")
for i, (doc, meta) in enumerate(zip(result2['retrieved_docs'], result2['metadatas']), 1):
    print(f"  [{i}] {meta.get('title', '')} ({meta.get('doc_category', '')})")

# 测试 3：写作实战 — 学生作文评估
print("\n" + "─" * 60)
print("\n[测试 3] 学生作文评估")
sample_essay = """成长的滋味

  成长，是每个人都要经历的过程。就像蝴蝶破茧而出，虽然痛苦，但最终会拥有美丽的翅膀。

  记得初二那年，我的数学成绩一直不好。每次考试后，看着试卷上刺眼的分数，我都感到无比沮丧。我开始怀疑自己，是不是天生就不是学习的料。

  有一天放学后，数学老师把我叫到办公室。我以为又要挨批评，低着头不敢看她。没想到她温和地说："我知道你最近很努力，只是方法可能不太对。来，我们一起看看你的错题。"那一刻，我的眼泪差点掉下来。

  从那以后，老师每天放学后都会抽出半小时帮我讲解错题。她教我用思维导图整理知识点，用错题本记录易错的地方。慢慢地，我的成绩开始提升。

  期末考试，我的数学考了85分，虽然不是最高的，但对我来说已经是一个巨大的进步。当我拿到试卷的那一刻，我终于明白了成长的滋味——它不是没有痛苦，而是在痛苦中有人愿意拉你一把，而你也要学会自己站起来。

  如今回想起来，那段艰难的日子反而是我最宝贵的财富。成长教会我的不仅是知识，更是面对困难时不放弃的勇气。"""

result3 = rag.query(
    question=f"""请评估以下初二学生的记叙文《成长的滋味》：

{sample_essay}

请从内容立意、结构安排、语言表达、细节描写四个维度评分（各25分），
指出优点和具体改进建议。""",
    role="资深初中语文教师",
    expertise="记叙文批改、作文评分、写作提升指导",
    score_threshold=0.25,
    top_k=8,
    temperature=0.4,
)
print(f"\n回答：\n{result3['answer']}")
print(f"\n检索到 {len(result3['retrieved_docs'])} 条参考资料")
for i, (doc, meta) in enumerate(zip(result3['retrieved_docs'], result3['metadatas']), 1):
    print(f"  [{i}] {meta.get('title', '')} ({meta.get('doc_category', '')})")

print("\n" + "=" * 60)