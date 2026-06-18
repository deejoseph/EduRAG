"""
EduRAG 试卷解析器测试脚本
测试 exam_parser 的结构化解析能力
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scripts.exam_parser import ExamPaperParser

# ── 模拟一份高考语文试卷文本 ──
SAMPLE_EXAM = """
2023年全国甲卷语文试题

一、现代文阅读（36分）
（一）论述类文本阅读（本题共3小题，9分）

阅读下面的文字，完成1～3题。

近年来，随着人工智能技术的快速发展，文学创作领域也出现了新的变化。AI写作工具能够根据给定的主题和风格，快速生成大量文本。然而，文学创作的本质并非简单的文字组合，而是创作者生命体验和思想情感的外化。

1. 下列关于原文内容的理解和分析，正确的一项是（3分）
A. AI写作工具已经完全取代了人类作家的创作
B. 文学创作的本质超越了简单的文字组合
C. 人工智能无法产生任何形式的情感表达
D. AI技术的发展对文学创作没有任何积极影响

2. 下列对原文论证的相关分析，不正确的一项是（3分）
A. 文章从AI技术发展入手引出文学创作的本质问题
B. 文章运用了对比论证的方法
C. 文章主要论述了AI写作的优越性
D. 文章强调了创作者生命体验的重要性

（二）实用类文本阅读（本题共3小题，12分）

阅读下面的文字，完成4～6题。

材料一：
中国空间站全面建成后，航天员在太空中开展了多项科学实验。其中，植物生长实验引起了广泛关注。

材料二：
据科研人员介绍，太空环境下的植物生长与地面有显著差异，微重力环境会影响植物的根系发育方向。

4. 根据材料一，下列关于中国空间站的说法正确的一项是（3分）
A. 空间站尚未建成
B. 航天员已开展科学实验
C. 植物生长实验未进行
D. 太空实验没有任何成果

5. 根据材料二，微重力环境对植物的影响主要表现在（3分）
A. 植物无法生长
B. 影响根系发育方向
C. 使植物生长更快
D. 对植物没有影响

二、古代诗文阅读（34分）
（一）文言文阅读（本题共4小题，19分）

阅读下面的文言文，完成10～13题。

陈涉世家（节选）

陈胜者，阳城人也，字涉。吴广者，阳夏人也，字叔。陈涉少时，尝与人佣耕，辍耕之垄上，怅恨久之，曰："苟富贵，无相忘。"

10. 下列对文中加点词语的解释，不正确的一项是（3分）
A. 佣耕：被雇佣耕地
B. 辍耕：停止耕地
C. 怅恨：惆怅遗憾
D. 苟富贵：如果富贵

三、语言文字运用（20分）

阅读下面的文字，完成17～18题。

春天来了，万物复苏。公园里的樱花______，吸引了大量游客前来观赏。

17. 填入文中横线处最恰当的成语是（3分）
A. 竞相开放
B. 落英缤纷
C. 花好月圆
D. 含苞待放

四、写作（60分）

22. 阅读下面的材料，根据要求写作。（60分）

有人说，人生就像一场旅行，重要的不是目的地，而是沿途的风景和看风景的心情。

请结合以上材料，以"旅途与风景"为主题，写一篇不少于800字的文章。
要求：选准角度，确定立意，明确文体，自拟标题；不要套作，不得抄袭。
"""


def test_parser():
    parser = ExamPaperParser()
    paper = parser.parse(SAMPLE_EXAM, source_file="2023年全国甲卷语文试题.pdf")

    print(f"\n{'='*60}")
    print(f"  试卷解析测试结果")
    print(f"{'='*60}")
    print(f"  标题: {paper.title}")
    print(f"  年份: {paper.year}")
    print(f"  考区: {paper.exam_region}")
    print(f"  学段: {paper.grade_level}")
    print(f"  科目: {paper.subject}")
    print(f"  题目数: {len(paper.questions)}")
    print(f"{'='*60}")

    # 打印每道题摘要
    for i, q in enumerate(paper.questions):
        text_preview = q.question_text[:80].replace('\n', ' ')
        score_info = f"（{q.score}分）" if q.score else ""
        print(f"\n  [{i+1}] 题号: {q.question_number} | 题型: {q.question_type}{score_info}")
        print(f"      所属: {q.section_name[:50]}")
        print(f"      内容: {text_preview}...")
        if q.options:
            print(f"      选项: {len(q.options)} 个")

    # 验证基本正确性
    print(f"\n{'='*60}")
    print(f"  验证检查:")
    
    assert paper.year == "2023", f"年份应为2023，实际: {paper.year}"
    print(f"  ✓ 年份正确: {paper.year}")

    assert paper.exam_region is not None, "考区不应为None"
    print(f"  ✓ 考区识别: {paper.exam_region}")

    assert len(paper.questions) >= 5, f"至少应有5道题，实际: {len(paper.questions)}"
    print(f"  ✓ 题目数量: {len(paper.questions)} >= 5")

    # 检查是否有作文题
    essay_questions = [q for q in paper.questions if q.question_type == "作文"]
    print(f"  ✓ 作文题数: {len(essay_questions)}")

    # 检查分值提取
    scored_questions = [q for q in paper.questions if q.score is not None]
    print(f"  ✓ 有分值的题: {len(scored_questions)}")
    for q in scored_questions:
        print(f"    - 题号{q.question_number}: {q.score}分")

    print(f"\n{'='*60}")
    print(f"  全部测试通过!")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    test_parser()
