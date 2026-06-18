"""
EduRAG 语文写作训练模块
提供审题、构思、写作辅助、评估四步流程
"""

import sys
import os
# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import logging
from typing import Dict, Any, Optional, List

from core.rag_pipeline import RAGPipeline
from core.db_manager import EduRAGDatabase
from core.llm_client import OllamaClient
from subjects.chinese.prompt_loader import (
    render_topic_analysis,
    render_outline,
    render_writing_assist,
    render_evaluation,
)

logger = logging.getLogger(__name__)


class ChineseWritingTrainer:
    """语文写作训练器"""
    
    def __init__(self, db=None, llm=None, collection_name="chinese_essays"):
        self.db = db or EduRAGDatabase()
        self.llm = llm or OllamaClient()
        # 确保集合存在（自动创建）
        if not self.db.collection_exists(collection_name):
            logger.info(f"创建集合: {collection_name}")
            self.db.create_collection(collection_name, metadata={"subject": "chinese", "description": "语文范文库"})
        # 创建 RAGPipeline 实例
        self.rag = RAGPipeline(
            db=self.db,
            llm=self.llm,
            default_collection=collection_name,
            default_top_k=8,
            default_score_threshold=0.25
        )
        self.collection_name = collection_name
        
    # ========== 1. 审题训练 ==========
    def analyze_topic(
        self,
        topic: str,
        grade: str = "初中",
        genre: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        审题分析
        
        Args:
            topic: 作文题目
            grade: 学段（小学/初中/高中）
            genre: 文体要求（记叙文/议论文/说明文等）
            
        Returns:
            包含审题结果的字典
        """
        # 使用 Prompt 模板
        rendered = render_topic_analysis(
            topic=topic,
            topic_type=genre or '',
            grade_level=grade,
        )

        result = self.rag.query(
            question=rendered['user_query'],
            system_prompt=rendered['system_prompt'],
            temperature=0.5
        )
        
        return {
            "topic": topic,
            "grade": grade,
            "analysis": result["answer"],
            "retrieved_examples": result["retrieved_docs"],
            "success": True
        }
    
    # ========== 2. 构思训练 ==========
    def generate_outline(
        self,
        topic: str,
        student_idea: Optional[str] = None,
        grade: str = "初中",
        genre: str = "记叙文"
    ) -> Dict[str, Any]:
        """
        生成作文提纲
        """
        # 使用 Prompt 模板
        rendered = render_outline(
            topic=topic,
            thesis=student_idea or '',
            style=genre,
            word_count=800,
        )

        result = self.rag.query(
            question=rendered['user_query'],
            system_prompt=rendered['system_prompt'],
            temperature=0.6
        )
        
        return {
            "topic": topic,
            "grade": grade,
            "genre": genre,
            "outline": result["answer"],
            "retrieved_materials": result["retrieved_docs"],
            "success": True
        }
    
    # ========== 3. 写作辅助（渐进式提示） ==========
    def assist_writing(
        self,
        topic: str,
        current_text: str,
        student_question: str,
        grade: str = "初中"
    ) -> Dict[str, Any]:
        """
        写作过程中提供辅助（不代写）
        """
        # 使用 Prompt 模板
        rendered = render_writing_assist(
            topic=topic,
            current_text=current_text[:500] + ('...' if len(current_text) > 500 else ''),
            help_type='polish',
            context=student_question,
        )

        result = self.rag.query(
            question=rendered['user_query'],
            system_prompt=rendered['system_prompt'],
            temperature=0.7
        )
        
        return {
            "topic": topic,
            "advice": result["answer"],
            "retrieved_tips": result["retrieved_docs"],
            "success": True
        }
    
    # ========== 4. 作文评估 ==========
    def evaluate_essay(
        self,
        topic: str,
        essay: str,
        grade: str = "初中",
        genre: str = "记叙文",
        scoring_criteria: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        多维度作文评估
        """
        default_criteria = {
            "content": 40,
            "structure": 25,
            "language": 20,
            "standard": 15
        }
        criteria = scoring_criteria or default_criteria
        
        # 构建评分维度
        scoring_rubric = [k.replace('_', ' ') for k in criteria.keys()]
        # 使用 Prompt 模板
        rendered = render_evaluation(
            essay=essay,
            topic=topic,
            grade_level=grade,
            scoring_rubric=list(criteria.keys()),
        )

        result = self.rag.query(
            question=rendered['user_query'],
            system_prompt=rendered['system_prompt'],
            temperature=0.4
        )
        
        import re
        score_match = re.search(r"总评分[：:]\s*(\d+)", result["answer"])
        total_score = int(score_match.group(1)) if score_match else None
        
        return {
            "topic": topic,
            "grade": grade,
            "total_score": total_score,
            "evaluation": result["answer"],
            "retrieved_standards": result["retrieved_docs"],
            "success": True
        }


# 简单测试
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    trainer = ChineseWritingTrainer()
    
    print("=== 审题测试 ===")
    res1 = trainer.analyze_topic("成长的滋味", grade="初中")
    print(res1["analysis"])
    
    print("\n=== 构思测试 ===")
    res2 = trainer.generate_outline("成长的滋味", student_idea="想写通过一次失败获得成长", grade="初中")
    print(res2["outline"])
    
    print("\n=== 写作辅助测试 ===")
    res3 = trainer.assist_writing(
        "成长的滋味",
        "那天考试我考砸了，心情很糟。",
        "如何描写失落的心情？",
        grade="初中"
    )
    print(res3["advice"])
    
    print("\n=== 评估测试 ===")
    sample_essay = """成长是每个人都要经历的。我记得有一次考试没考好，妈妈安慰我。从那以后我努力学习，终于考好了。这就是成长的滋味。"""
    res4 = trainer.evaluate_essay("成长的滋味", sample_essay, grade="初中")
    print(res4["evaluation"])