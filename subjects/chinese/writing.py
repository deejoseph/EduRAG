"""
EduRAG 语文写作训练模块
提供审题、构思、写作辅助、评估四步流程
支持多AI并行生成和播客素材导出
"""

import sys
import os
# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import logging
from typing import Dict, Any, Optional, List
from concurrent.futures import ThreadPoolExecutor, as_completed

from core.rag_pipeline import RAGPipeline
from core.db_manager import EduRAGDatabase
from core.llm_client import OllamaClient
from subjects.chinese.prompt_loader import (
    render_topic_analysis,
    render_outline,
    render_writing_assist,
    render_evaluation,
)
from podcast.material_manager import get_podcast_manager

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
    
    # ========== 播客素材生成功能 ==========
    
    def _generate_with_model(
        self,
        model_name: str,
        query_func,
        **kwargs
    ) -> Dict[str, Any]:
        """
        使用指定模型生成内容（用于多AI并行）
        
        Args:
            model_name: 模型名称
            query_func: 查询函数
            **kwargs: 传递给函数的参数
            
        Returns:
            包含结果和模型信息的字典
        """
        try:
            # 创建独立的LLM客户端实例
            llm = OllamaClient(model=model_name)
            rag = RAGPipeline(
                db=self.db,
                llm=llm,
                default_collection=self.collection_name,
                default_top_k=kwargs.get('top_k', 8),
                default_score_threshold=kwargs.get('score_threshold', 0.25)
            )
            
            # 执行查询
            result = query_func(rag, **kwargs)
            
            return {
                "ai_model": model_name,
                "content": result.get("answer", ""),
                "success": True,
                "error": None
            }
        except Exception as e:
            logger.error(f"模型 {model_name} 生成失败: {e}")
            return {
                "ai_model": model_name,
                "content": "",
                "success": False,
                "error": str(e)
            }
    
    def generate_multi_ai_analysis(
        self,
        topic: str,
        models: List[str] = None,
        grade: str = "初中",
        genre: Optional[str] = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        多AI并行生成审题分析
        
        Args:
            topic: 作文题目
            models: AI模型列表，默认使用配置的多个模型
            grade: 学段
            genre: 文体
            **kwargs: 其他参数
            
        Returns:
            多个AI的生成结果列表
        """
        if models is None:
            # 默认使用2个差异化模型（避免同质化）
            models = ["qwen3:8b", "gemma3:4b"]
        
        def query_func(rag, **kw):
            rendered = render_topic_analysis(
                topic=kw['topic'],
                topic_type=kw.get('genre', ''),
                grade_level=kw.get('grade', '初中'),
            )
            result = rag.query(
                question=rendered['user_query'],
                system_prompt=rendered['system_prompt'],
                temperature=0.5
            )
            return {"answer": result["answer"]}
        
        results = []
        with ThreadPoolExecutor(max_workers=len(models)) as executor:
            futures = {
                executor.submit(
                    self._generate_with_model,
                    model,
                    query_func,
                    topic=topic,
                    grade=grade,
                    genre=genre,
                    **kwargs
                ): model
                for model in models
            }
            
            for future in as_completed(futures):
                result = future.result()
                results.append(result)
        
        return results
    
    def generate_multi_ai_outline(
        self,
        topic: str,
        models: List[str] = None,
        student_idea: Optional[str] = None,
        grade: str = "初中",
        genre: str = "记叙文",
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        多AI并行生成构思提纲
        """
        if models is None:
            models = ["qwen3:8b", "gemma3:4b"]
        
        def query_func(rag, **kw):
            rendered = render_outline(
                topic=kw['topic'],
                thesis=kw.get('student_idea', ''),
                style=kw.get('genre', '记叙文'),
                word_count=800,
            )
            result = rag.query(
                question=rendered['user_query'],
                system_prompt=rendered['system_prompt'],
                temperature=0.6
            )
            return {"answer": result["answer"]}
        
        results = []
        with ThreadPoolExecutor(max_workers=len(models)) as executor:
            futures = {
                executor.submit(
                    self._generate_with_model,
                    model,
                    query_func,
                    topic=topic,
                    student_idea=student_idea,
                    grade=grade,
                    genre=genre,
                    **kwargs
                ): model
                for model in models
            }
            
            for future in as_completed(futures):
                result = future.result()
                results.append(result)
        
        return results
    
    def generate_full_essay(
        self,
        topic: str,
        outline: str,
        models: List[str] = None,
        grade: str = "初中",
        genre: str = "议论文",
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        基于立意和提纲生成完整范文（新增功能）
        
        Args:
            topic: 作文题目
            outline: 构思提纲
            models: AI模型列表
            grade: 学段
            genre: 文体
            **kwargs: 其他参数
            
        Returns:
            多个AI生成的范文列表
        """
        if models is None:
            models = ["qwen3:8b", "gemma3:4b"]
        
        def query_func(rag, **kw):
            # 使用写作辅助接口，但提示生成全文
            prompt = f"""请根据以下题目和提纲，写一篇完整的高考{kw.get('genre', '议论文')}范文：

题目：{kw['topic']}

提纲：
{kw['outline']}

写作要求：
1. 这是一篇高中生写的作文，不是商业文档或报告，请用自然流畅的散文体写作
2. 段落之间自然过渡，不要使用编号、列表、小标题等格式
3. 结构完整：引论（开头）→ 本论（主体段落）→ 结论（结尾）
4. 每个主体段落围绕一个分论点展开，包含论据和论证
5. 语言要有文采，适当使用修辞手法（比喻、排比、引用等）
6. 字数在800-1000字之间
7. 符合高考作文评分标准（立意深刻、内容充实、语言流畅）

请直接输出作文全文，不要添加任何标题、编号或说明文字："""
            
            result = rag.query(
                question=prompt,
                system_prompt="你是一位资深高中语文教师，擅长指导学生写作高考满分作文。你的写作风格自然流畅，富有文采，像真实的高考高分作文，而不是商业文档或报告。",
                temperature=0.7
            )
            return {"answer": result["answer"]}
        
        results = []
        with ThreadPoolExecutor(max_workers=len(models)) as executor:
            futures = {
                executor.submit(
                    self._generate_with_model,
                    model,
                    query_func,
                    topic=topic,
                    outline=outline,
                    grade=grade,
                    genre=genre,
                    **kwargs
                ): model
                for model in models
            }
            
            for future in as_completed(futures):
                result = future.result()
                results.append(result)
        
        return results
    
    def generate_multi_ai_evaluation(
        self,
        topic: str,
        essay: str,
        models: List[str] = None,
        grade: str = "初中",
        genre: str = "记叙文",
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        多AI并行生成作文评估
        """
        if models is None:
            models = ["qwen3:8b", "gemma3:4b"]
        
        def query_func(rag, **kw):
            rendered = render_evaluation(
                essay=kw['essay'],
                topic=kw.get('topic', ''),
                grade_level=kw.get('grade', '初中'),
                scoring_rubric=['内容立意', '结构安排', '语言表达', '发展等级'],
            )
            result = rag.query(
                question=rendered['user_query'],
                system_prompt=rendered['system_prompt'],
                temperature=0.4
            )
            return {"answer": result["answer"]}
        
        results = []
        with ThreadPoolExecutor(max_workers=len(models)) as executor:
            futures = {
                executor.submit(
                    self._generate_with_model,
                    model,
                    query_func,
                    topic=topic,
                    essay=essay,
                    grade=grade,
                    genre=genre,
                    **kwargs
                ): model
                for model in models
            }
            
            for future in as_completed(futures):
                result = future.result()
                results.append(result)
        
        return results
    
    def export_to_podcast(
        self,
        stage: str,
        topic: str,
        content: str,
        ai_model: str = "default",
        metadata: Optional[Dict] = None
    ) -> str:
        """
        导出单个阶段的素材到播客模块
        
        Args:
            stage: 阶段名称 (analysis/outline/essay/evaluation)
            topic: 作文题目
            content: AI生成的内容
            ai_model: 使用的AI模型
            metadata: 额外元数据
            
        Returns:
            material_id: 素材ID
        """
        manager = get_podcast_manager()
        material_id = manager.add_stage_material(
            stage=stage,
            topic=topic,
            content=content,
            ai_model=ai_model,
            metadata=metadata
        )
        return material_id


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