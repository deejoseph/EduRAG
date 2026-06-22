"""
写作训练 API 路由
提供审题、构思、写作辅助、作文评估四个接口
支持多AI并行生成和播客素材导出
"""

import logging
import time
from pathlib import Path
from flask import Blueprint, request, jsonify, current_app
from typing import List, Optional

from subjects.chinese.prompt_loader import (
    render_topic_analysis,
    render_outline,
    render_writing_assist,
    render_evaluation,
)
from api.routes import build_where_filter
from podcast.material_manager import get_podcast_manager
from core.db_manager import EduRAGDatabase

logger = logging.getLogger(__name__)

writing_bp = Blueprint('writing', __name__)


def get_rag():
    """获取共享的 RAG 实例"""
    return current_app.config['edurag']['rag']


def error_response(message: str, code: int = 400):
    """统一错误响应"""
    return jsonify({'error': message}), code


def success_response(data: dict):
    """统一成功响应"""
    return jsonify({
        'success': True,
        **data,
    })


def _extract_search_params(data: dict):
    """提取过滤条件和重排序参数"""
    filters = data.get('filters', {})
    where_filter = build_where_filter(
        year=filters.get('year'),
        exam_region=filters.get('exam_region'),
        doc_category=filters.get('doc_category'),
        file_type=filters.get('file_type'),
        question_type=filters.get('question_type'),
        grade_level=filters.get('grade_level'),
        subject=filters.get('subject'),
        source_type=filters.get('source_type'),
    )
    rerank = data.get('rerank', None)
    return where_filter, rerank


# ─────────────────────────────────────────────────────────
# POST /writing/analyze  审题分析
# ─────────────────────────────────────────────────────────
@writing_bp.route('/analyze', methods=['POST'])
def analyze():
    """
    审题分析接口
    分析作文题目，提供立意方向和写作思路

    请求体：
    {
        "topic": "作文题目（必填）",
        "topic_type": "题目类型：命题/材料/话题（可选）",
        "grade_level": "年级：初中/高中（可选，默认高中）",
        "top_k": "参考资料数量（可选，默认 8）",
        "score_threshold": "相似度阈值（可选，默认 0.25）"
    }

    响应体：
    {
        "success": true,
        "answer": "审题分析内容",
        "references": [{"text": "...", "metadata": {...}}],
        "ref_count": 8
    }
    """
    data = request.get_json()
    if not data:
        return error_response("请求体不能为空")

    topic = data.get('topic')
    if not topic:
        return error_response("必须提供 topic 字段")

    topic_type = data.get('topic_type', '')
    grade_level = data.get('grade_level', '高中')
    top_k = data.get('top_k', 8)
    score_threshold = data.get('score_threshold', 0.25)
    where_filter, rerank = _extract_search_params(data)

    # 使用 Prompt 模板渲染
    rendered = render_topic_analysis(
        topic=topic,
        topic_type=topic_type,
        grade_level=grade_level,
    )

    try:
        rag = get_rag()
        result = rag.query(
            question=rendered['user_query'],
            system_prompt=rendered['system_prompt'],
            top_k=top_k,
            score_threshold=score_threshold,
            where=where_filter,
            rerank=rerank,
            temperature=0.5,
        )

        refs = [
            {
                'text': doc[:200] + ('...' if len(doc) > 200 else ''),
                'metadata': meta,
            }
            for doc, meta in zip(result['retrieved_docs'], result['metadatas'])
        ]

        return success_response({
            'answer': result['answer'],
            'references': refs,
            'ref_count': len(refs),
        })

    except Exception as e:
        logger.error(f"审题分析失败: {e}")
        return error_response(f"服务端错误: {e}", 500)


# ─────────────────────────────────────────────────────────
# POST /writing/outline  构思提纲
# ─────────────────────────────────────────────────────────
@writing_bp.route('/outline', methods=['POST'])
def outline():
    """
    构思提纲接口
    根据题目和立意生成文章结构大纲

    请求体：
    {
        "topic": "作文题目（必填）",
        "thesis": "选定的立意方向（可选，不传则由 LLM 自行决定）",
        "style": "文体：议论文/记叙文/散文（可选，默认议论文）",
        "word_count": "目标字数（可选，默认 800）",
        "top_k": "参考资料数量（可选，默认 8）",
        "score_threshold": "相似度阈值（可选，默认 0.25）"
    }

    响应体：
    {
        "success": true,
        "answer": "构思提纲内容",
        "references": [...],
        "ref_count": 8
    }
    """
    data = request.get_json()
    if not data:
        return error_response("请求体不能为空")

    topic = data.get('topic')
    if not topic:
        return error_response("必须提供 topic 字段")

    thesis = data.get('thesis', '')
    style = data.get('style', '议论文')
    word_count = data.get('word_count', 800)
    top_k = data.get('top_k', 8)
    score_threshold = data.get('score_threshold', 0.25)
    where_filter, rerank = _extract_search_params(data)

    # 使用 Prompt 模板渲染
    rendered = render_outline(
        topic=topic,
        thesis=thesis,
        style=style,
        word_count=word_count,
    )

    try:
        rag = get_rag()
        result = rag.query(
            question=rendered['user_query'],
            system_prompt=rendered['system_prompt'],
            top_k=top_k,
            score_threshold=score_threshold,
            where=where_filter,
            rerank=rerank,
            temperature=0.6,
        )

        refs = [
            {
                'text': doc[:200] + ('...' if len(doc) > 200 else ''),
                'metadata': meta,
            }
            for doc, meta in zip(result['retrieved_docs'], result['metadatas'])
        ]

        return success_response({
            'answer': result['answer'],
            'references': refs,
            'ref_count': len(refs),
        })

    except Exception as e:
        logger.error(f"构思提纲生成失败: {e}")
        return error_response(f"服务端错误: {e}", 500)


# ─────────────────────────────────────────────────────────
# POST /writing/assist  写作辅助
# ─────────────────────────────────────────────────────────
@writing_bp.route('/assist', methods=['POST'])
def assist():
    """
    写作辅助接口
    在写作过程中提供局部优化建议（润色段落、修辞建议等）

    请求体：
    {
        "current_text": "当前已写的内容（必填）",
        "topic": "作文题目（必填）",
        "help_type": "帮助类型：polish 润色 / continue 续写 / rhetoric 修辞 / transition 过渡（可选，默认 polish）",
        "context": "额外上下文说明（可选）",
        "top_k": "参考资料数量（可选，默认 8）",
        "score_threshold": "相似度阈值（可选，默认 0.25）"
    }

    响应体：
    {
        "success": true,
        "answer": "写作辅助建议",
        "references": [...],
        "ref_count": 8
    }
    """
    data = request.get_json()
    if not data:
        return error_response("请求体不能为空")

    current_text = data.get('current_text')
    topic = data.get('topic')
    if not current_text:
        return error_response("必须提供 current_text 字段")
    if not topic:
        return error_response("必须提供 topic 字段")

    help_type = data.get('help_type', 'polish')
    context = data.get('context', '')
    top_k = data.get('top_k', 8)
    score_threshold = data.get('score_threshold', 0.25)
    where_filter, rerank = _extract_search_params(data)

    # 使用 Prompt 模板渲染
    rendered = render_writing_assist(
        topic=topic,
        current_text=current_text,
        help_type=help_type,
        context=context,
    )

    try:
        rag = get_rag()
        result = rag.query(
            question=rendered['user_query'],
            system_prompt=rendered['system_prompt'],
            top_k=top_k,
            score_threshold=score_threshold,
            where=where_filter,
            rerank=rerank,
            temperature=0.7,
        )

        refs = [
            {
                'text': doc[:200] + ('...' if len(doc) > 200 else ''),
                'metadata': meta,
            }
            for doc, meta in zip(result['retrieved_docs'], result['metadatas'])
        ]

        return success_response({
            'answer': result['answer'],
            'references': refs,
            'ref_count': len(refs),
        })

    except Exception as e:
        logger.error(f"写作辅助失败: {e}")
        return error_response(f"服务端错误: {e}", 500)


# ─────────────────────────────────────────────────────────
# POST /writing/evaluate  作文评估
# ─────────────────────────────────────────────────────────
@writing_bp.route('/evaluate', methods=['POST'])
def evaluate():
    """
    作文评估接口
    对学生作文进行多维度评分和点评

    请求体：
    {
        "essay": "学生作文全文（必填）",
        "topic": "作文题目（可选）",
        "grade_level": "年级：初中/高中（可选，默认高中）",
        "scoring_rubric": "评分维度列表（可选）",
        "top_k": "参考资料数量（可选，默认 8）",
        "score_threshold": "相似度阈值（可选，默认 0.25）"
    }

    响应体：
    {
        "success": true,
        "answer": "评估报告",
        "references": [...],
        "ref_count": 8
    }
    """
    data = request.get_json()
    if not data:
        return error_response("请求体不能为空")

    essay = data.get('essay')
    if not essay:
        return error_response("必须提供 essay 字段")

    topic = data.get('topic', '')
    grade_level = data.get('grade_level', '高中')
    scoring_rubric = data.get('scoring_rubric', [
        '内容立意', '结构安排', '语言表达', '发展等级'
    ])
    top_k = data.get('top_k', 8)
    score_threshold = data.get('score_threshold', 0.25)
    where_filter, rerank = _extract_search_params(data)

    # 使用 Prompt 模板渲染
    rendered = render_evaluation(
        essay=essay,
        topic=topic,
        grade_level=grade_level,
        scoring_rubric=scoring_rubric,
    )

    try:
        rag = get_rag()
        result = rag.query(
            question=rendered['user_query'],
            system_prompt=rendered['system_prompt'],
            top_k=top_k,
            score_threshold=score_threshold,
            where=where_filter,
            rerank=rerank,
            temperature=0.4,
        )

        refs = [
            {
                'text': doc[:200] + ('...' if len(doc) > 200 else ''),
                'metadata': meta,
            }
            for doc, meta in zip(result['retrieved_docs'], result['metadatas'])
        ]

        return success_response({
            'answer': result['answer'],
            'references': refs,
            'ref_count': len(refs),
        })

    except Exception as e:
        logger.error(f"作文评估失败: {e}")
        return error_response(f"服务端错误: {e}", 500)


# ─────────────────────────────────────────────────────────
# POST /writing/multi-ai/analyze  多AI并行审题分析
# ─────────────────────────────────────────────────────────
@writing_bp.route('/multi-ai/analyze', methods=['POST'])
def multi_ai_analyze():
    """
    多AI并行生成审题分析
    
    请求体：
    {
        "topic": "作文题目（必填）",
        "models": ["qwen2.5:7b", "qwen3:8b", "gemma3:4b"]（可选，默认3个模型）,
        "grade_level": "年级（可选，默认高中）",
        "topic_type": "题目类型（可选）"
    }
    
    响应体：
    {
        "success": true,
        "results": [
            {"ai_model": "qwen2.5:7b", "content": "...", "success": true},
            {"ai_model": "qwen3:8b", "content": "...", "success": true}
        ],
        "count": 3
    }
    """
    data = request.get_json()
    if not data:
        return error_response("请求体不能为空")
    
    topic = data.get('topic')
    if not topic:
        return error_response("必须提供 topic 字段")
    
    models = data.get('models', ["qwen3:8b", "gemma3:4b"])
    grade_level = data.get('grade_level', '高中')
    topic_type = data.get('topic_type', '')
    
    try:
        trainer = current_app.config['edurag']['chinese_trainer']
        results = trainer.generate_multi_ai_analysis(
            topic=topic,
            models=models,
            grade=grade_level,
            genre=topic_type
        )
        
        return success_response({
            'results': results,
            'count': len(results)
        })
    
    except Exception as e:
        logger.error(f"多AI审题分析失败: {e}")
        return error_response(f"服务端错误: {e}", 500)


# ─────────────────────────────────────────────────────────
# POST /writing/multi-ai/outline  多AI并行构思提纲
# ─────────────────────────────────────────────────────────
@writing_bp.route('/multi-ai/outline', methods=['POST'])
def multi_ai_outline():
    """
    多AI并行生成构思提纲
    
    请求体：
    {
        "topic": "作文题目（必填）",
        "thesis": "立意方向（可选）",
        "style": "文体（可选，默认议论文）",
        "models": [...]（可选）
    }
    """
    data = request.get_json()
    if not data:
        return error_response("请求体不能为空")
    
    topic = data.get('topic')
    if not topic:
        return error_response("必须提供 topic 字段")
    
    models = data.get('models', ["qwen3:8b", "gemma3:4b"])
    thesis = data.get('thesis', '')
    style = data.get('style', '议论文')
    
    try:
        trainer = current_app.config['edurag']['chinese_trainer']
        results = trainer.generate_multi_ai_outline(
            topic=topic,
            models=models,
            student_idea=thesis,
            genre=style
        )
        
        return success_response({
            'results': results,
            'count': len(results)
        })
    
    except Exception as e:
        logger.error(f"多AI构思提纲失败: {e}")
        return error_response(f"服务端错误: {e}", 500)


# ─────────────────────────────────────────────────────────
# POST /writing/generate-essay  基于提纲生成范文（新功能）
# ─────────────────────────────────────────────────────────
@writing_bp.route('/generate-essay', methods=['POST'])
def generate_essay():
    """
    基于立意和提纲生成完整范文
    
    请求体：
    {
        "topic": "作文题目（必填）",
        "outline": "构思提纲（必填）",
        "genre": "文体（可选，默认议论文）",
        "models": [...]（可选）
    }
    """
    data = request.get_json()
    if not data:
        return error_response("请求体不能为空")
    
    topic = data.get('topic')
    outline = data.get('outline')
    if not topic or not outline:
        return error_response("必须提供 topic 和 outline 字段")
    
    models = data.get('models', ["qwen3:8b", "gemma3:4b"])
    genre = data.get('genre', '议论文')
    
    try:
        trainer = current_app.config['edurag']['chinese_trainer']
        results = trainer.generate_full_essay(
            topic=topic,
            outline=outline,
            models=models,
            genre=genre
        )
        
        return success_response({
            'results': results,
            'count': len(results)
        })
    
    except Exception as e:
        logger.error(f"生成范文失败: {e}")
        return error_response(f"服务端错误: {e}", 500)


# ─────────────────────────────────────────────────────────
# POST /writing/multi-ai/evaluate  多AI并行作文评估
# ─────────────────────────────────────────────────────────
@writing_bp.route('/multi-ai/evaluate', methods=['POST'])
def multi_ai_evaluate():
    """
    多AI并行生成作文评估
    
    请求体：
    {
        "essay": "学生作文全文（必填）",
        "topic": "作文题目（可选）",
        "models": [...]（可选）
    }
    """
    data = request.get_json()
    if not data:
        return error_response("请求体不能为空")
    
    essay = data.get('essay')
    if not essay:
        return error_response("必须提供 essay 字段")
    
    topic = data.get('topic', '')
    models = data.get('models', ["qwen3:8b", "gemma3:4b"])
    
    try:
        trainer = current_app.config['edurag']['chinese_trainer']
        results = trainer.generate_multi_ai_evaluation(
            topic=topic,
            essay=essay,
            models=models
        )
        
        return success_response({
            'results': results,
            'count': len(results)
        })
    
    except Exception as e:
        logger.error(f"多AI作文评估失败: {e}")
        return error_response(f"服务端错误: {e}", 500)


# ─────────────────────────────────────────────────────────
# POST /writing/export-to-podcast  导出素材到播客模块
# ─────────────────────────────────────────────────────────
@writing_bp.route('/export-to-podcast', methods=['POST'])
def export_to_podcast():
    """
    将当前阶段的AI生成结果导出到播客模块
    
    请求体：
    {
        "stage": "阶段名称 (analysis/outline/essay/evaluation)（必填）",
        "topic": "作文题目（必填）",
        "content": "AI生成的内容（必填）",
        "ai_model": "使用的AI模型（必填）",
        "metadata": {...}（可选）
    }
    
    响应体：
    {
        "success": true,
        "material_id": "POD_20260121_123456_analysis"
    }
    """
    data = request.get_json()
    if not data:
        return error_response("请求体不能为空")
    
    stage = data.get('stage')
    topic = data.get('topic')
    content = data.get('content')
    ai_model = data.get('ai_model', 'default')
    
    if not stage or not topic or not content:
        return error_response("必须提供 stage、topic 和 content 字段")
    
    # 验证阶段名称
    valid_stages = ['analysis', 'outline', 'essay', 'evaluation']
    if stage not in valid_stages:
        return error_response(f"stage 必须是以下之一: {valid_stages}")
    
    try:
        manager = get_podcast_manager()
        material_id = manager.add_stage_material(
            stage=stage,
            topic=topic,
            content=content,
            ai_model=ai_model,
            metadata=data.get('metadata', {})
        )
        
        return success_response({
            'material_id': material_id,
            'message': f'素材已导出到播客模块'
        })
    
    except Exception as e:
        logger.error(f"导出播客素材失败: {e}")
        return error_response(f"服务端错误: {e}", 500)


@writing_bp.route('/podcast-scripts', methods=['GET'])
def get_podcast_scripts():
    """
    获取播客文案列表
    
    查询参数：
    - topic: 主题过滤（可选）
    - status: 状态过滤（draft/completed/archived）
    - stage: 阶段过滤（shenti/gousi/xiezuo/pinggu）
    - limit: 返回数量限制（默认50）
    
    响应体：
    {
        "success": true,
        "scripts": [
            {
                "script_id": "uuid",
                "title": "标题",
                "topic": "主题",
                "version": 1,
                "status": "draft",
                "stage": "shenti",
                "created_at": "2024-01-01 12:00:00",
                "materials_count": 3
            }
        ],
        "count": 10
    }
    """
    try:
        from flask import current_app
        from podcast.script_state_manager import get_script_state_manager
        app_config = current_app.config.get('edurag', {})
        db = app_config.get('db')
        
        if not db:
            return error_response("数据库未初始化", 500)
        
        # 获取查询参数
        topic = request.args.get('topic')
        status_filter = request.args.get('status')  # 前端传入的status过滤
        stage_filter = request.args.get('stage')  # 前端传入的stage过滤
        limit = int(request.args.get('limit', 50))
        
        # 构建where条件（不再使用status过滤，因为要从JSON文件读取）
        where_filter = {'type': 'podcast_script'}
        if topic:
            where_filter['topic'] = topic
        
        # 查询所有符合条件的文案
        # 检查集合是否存在
        if not db.collection_exists('podcast_scripts'):
            logger.info("播客文案集合尚未创建，返回空列表")
            return success_response({
                'scripts': [],
                'count': 0
            })
        
        collection = db.get_collection('podcast_scripts')
        results = collection.get(
            where=where_filter,
            limit=limit,
            include=['metadatas']
        )
        
        # 从状态管理器获取所有文案的最新状态和阶段
        state_mgr = get_script_state_manager()
        all_states = state_mgr.get_all_states()
        
        # 提取元数据并按时间排序，同时更新状态和阶段
        scripts = []
        for metadata in results['metadatas']:
            script_id = metadata.get('script_id')
            
            # 从 JSON 文件中获取最新状态和阶段，如果没有则使用 ChromaDB 中的默认值
            latest_status = all_states.get(script_id, {}).get('status', metadata.get('status', 'draft'))
            latest_stage = all_states.get(script_id, {}).get('stage', None)
            
            # 如果前端传入了status过滤，在这里进行过滤
            if status_filter and latest_status != status_filter:
                continue
            
            # 如果前端传入了stage过滤，在这里进行过滤
            if stage_filter and latest_stage != stage_filter:
                continue
            
            scripts.append({
                'script_id': script_id,
                'title': metadata.get('title', '未命名'),
                'topic': metadata.get('topic', '未知'),
                'version': metadata.get('version', 1),
                'parent_id': metadata.get('parent_id'),
                'status': latest_status,  # 使用最新状态
                'stage': latest_stage,  # 添加阶段字段
                'created_at': metadata.get('created_at'),
                'updated_at': metadata.get('updated_at'),
                'materials_count': metadata.get('materials_count', 0),
                'model': metadata.get('model', 'unknown')
            })
        
        # 按时间戳降序排序（最新的在前）
        scripts.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        logger.info(f"获取到 {len(scripts)} 个播客文案")
        
        return success_response({
            'scripts': scripts,
            'count': len(scripts)
        })
    
    except Exception as e:
        logger.error(f"获取播客文案列表失败: {e}")
        return error_response(f"服务端错误: {e}", 500)


@writing_bp.route('/podcast-scripts/<script_id>', methods=['GET'])
def get_podcast_script(script_id: str):
    """
    获取单个播客文案内容
    
    路径参数：
    - script_id: 文案ID
    
    响应体：
    {
        "success": true,
        "script": {
            "script_id": "uuid",
            "content": "文案内容",
            "title": "标题",
            "topic": "主题",
            "version": 1,
            "status": "draft",
            "created_at": "2024-01-01 12:00:00"
        }
    }
    """
    try:
        from flask import current_app
        app_config = current_app.config.get('edurag', {})
        db = app_config.get('db')
        
        if not db:
            return error_response("数据库未初始化", 500)
        
        # 检查集合是否存在
        if not db.collection_exists('podcast_scripts'):
            return error_response(f"文案 {script_id} 不存在", 404)
        
        # 查询指定ID的文案
        collection = db.get_collection('podcast_scripts')
        results = collection.get(
            where={'script_id': script_id},
            include=['metadatas', 'documents']
        )
        
        if not results['metadatas']:
            return error_response(f"文案 {script_id} 不存在", 404)
        
        metadata = results['metadatas'][0]
        content = results['documents'][0] if results['documents'] else ''
        
        script_data = {
            'script_id': metadata.get('script_id'),
            'content': content,
            'title': metadata.get('title', '未命名'),
            'topic': metadata.get('topic', '未知'),
            'version': metadata.get('version', 1),
            'parent_id': metadata.get('parent_id'),
            'status': metadata.get('status', 'draft'),
            'created_at': metadata.get('created_at'),
            'updated_at': metadata.get('updated_at'),
            'materials_count': metadata.get('materials_count', 0),
            'model': metadata.get('model', 'unknown')
        }
        
        return success_response({'script': script_data})
    
    except Exception as e:
        logger.error(f"获取播客文案失败: {e}")
        return error_response(f"服务端错误: {e}", 500)


@writing_bp.route('/podcast-scripts/<script_id>', methods=['DELETE'])
def delete_podcast_script(script_id: str):
    """
    删除播客文案
    
    路径参数：
    - script_id: 文案ID
    
    响应体：
    {
        "success": true,
        "message": "文案已删除"
    }
    """
    try:
        from flask import current_app
        app_config = current_app.config.get('edurag', {})
        db = app_config.get('db')
        
        if not db:
            return error_response("数据库未初始化", 500)
        
        # 检查集合是否存在
        if not db.collection_exists('podcast_scripts'):
            return error_response(f"文案 {script_id} 不存在", 404)
        
        # 删除指定ID的文案
        collection = db.get_collection('podcast_scripts')
        results = collection.get(
            where={'script_id': script_id},
            include=[]
        )
        
        if not results['ids']:
            return error_response(f"文案 {script_id} 不存在", 404)
        
        # 删除
        collection.delete(ids=results['ids'])
        logger.info(f"播客文案已删除: {script_id}")
        
        return success_response({'message': '文案已删除'})
    
    except Exception as e:
        logger.error(f"删除播客文案失败: {e}")
        return error_response(f"服务端错误: {e}", 500)


@writing_bp.route('/podcast-scripts/<script_id>/duplicate', methods=['POST'])
def duplicate_podcast_script(script_id: str):
    """
    复制播客文案（用于二次创作）
    
    路径参数：
    - script_id: 原文案ID
    
    响应体：
    {
        "success": true,
        "new_script_id": "新的文案ID",
        "version": 2
    }
    """
    try:
        from flask import current_app
        app_config = current_app.config.get('edurag', {})
        db = app_config.get('db')
        
        if not db:
            return error_response("数据库未初始化", 500)
        
        # 检查集合是否存在
        if not db.collection_exists('podcast_scripts'):
            return error_response(f"文案 {script_id} 不存在", 404)
        
        # 获取原文案
        collection = db.get_collection('podcast_scripts')
        results = collection.get(
            where={'script_id': script_id},
            include=['metadatas', 'documents']
        )
        
        if not results['metadatas']:
            return error_response(f"文案 {script_id} 不存在", 404)
        
        original_metadata = results['metadatas'][0]
        original_content = results['documents'][0] if results['documents'] else ''
        
        # 生成新ID
        import time
        import uuid
        new_script_id = str(uuid.uuid4())
        timestamp = int(time.time() * 1000)
        
        # 创建副本，版本号+1
        new_version = original_metadata.get('version', 1) + 1
        new_metadata = dict(original_metadata)
        new_metadata.update({
            'script_id': new_script_id,
            'version': new_version,
            'parent_id': script_id or '',  # ChromaDB 不支持 None，用空字符串代替
            'title': f"{original_metadata.get('title', '未命名')} (副本v{new_version})",
            'status': 'draft',
            'created_at': time.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': time.strftime('%Y-%m-%d %H:%M:%S'),
            'timestamp': timestamp
        })
        
        # 保存副本
        db.add_documents(
            collection_name='podcast_scripts',
            documents=[original_content],
            metadatas=[new_metadata],
            ids=[f'script_{new_script_id}']
        )
        
        logger.info(f"播客文案已复制: {script_id} -> {new_script_id} (v{new_version})")
        
        return success_response({
            'new_script_id': new_script_id,
            'version': new_version,
            'title': new_metadata['title']
        })
    
    except Exception as e:
        logger.error(f"复制播客文案失败: {e}")
        return error_response(f"服务端错误: {e}", 500)


# ─────────────────────────────────────────────────────────
# GET /writing/podcast-materials  获取播客素材列表
# ─────────────────────────────────────────────────────────
@writing_bp.route('/podcast-materials', methods=['GET'])
def list_podcast_materials():
    """
    获取已导出的播客素材列表
    
    查询参数：
    - topic: 按题目过滤
    - stage: 按阶段过滤
    - status: 按状态过滤
    
    响应体：
    {
        "success": true,
        "materials": [...],
        "count": 10
    }
    """
    try:
        topic = request.args.get('topic')
        stage = request.args.get('stage')
        status = request.args.get('status')
        
        manager = get_podcast_manager()
        materials = manager.list_materials(
            topic=topic,
            stage=stage,
            status=status
        )
        
        return success_response({
            'materials': materials,
            'count': len(materials)
        })
    
    except Exception as e:
        logger.error(f"获取播客素材列表失败: {e}")
        return error_response(f"服务端错误: {e}", 500)


@writing_bp.route('/podcast-materials/<material_id>', methods=['DELETE'])
def delete_podcast_material(material_id: str):
    """
    删除单个播客素材
    
    路径参数：
    - material_id: 素材ID
    
    响应体：
    {
        "success": true,
        "message": "素材已删除"
    }
    """
    try:
        manager = get_podcast_manager()
        success = manager.delete_material(material_id)
        
        if success:
            return success_response({'message': '素材已删除'})
        else:
            return error_response(f"素材 {material_id} 不存在", 404)
    
    except Exception as e:
        logger.error(f"删除播客素材失败: {e}")
        return error_response(f"服务端错误: {e}", 500)


@writing_bp.route('/podcast-generate', methods=['POST'])
def generate_podcast_script():
    """
    基于选中的素材生成播客文案
    
    请求体：
    {
        "material_ids": ["POD_20260621_154353_analysis", ...],
        "prompt": "请将这些素材整理成一段播客对话，风格轻松有趣",
        "model": "qwen3:8b"  # 可选，默认 qwen3:8b
    }
    
    响应体：
    {
        "success": true,
        "script": "生成的播客文案内容...",
        "ai_model": "qwen3:8b"
    }
    """
    data = request.get_json()
    if not data:
        return error_response("请求体不能为空")
    
    material_ids = data.get('material_ids')
    if not material_ids or not isinstance(material_ids, list) or len(material_ids) == 0:
        return error_response("必须提供 material_ids 数组")
    
    prompt = data.get('prompt', '请将这些素材整理成一段播客对话，风格轻松有趣')
    model = data.get('model', 'qwen3:8b')
    
    try:
        # 获取所有选中的素材
        manager = get_podcast_manager()
        materials = []
        for material_id in material_ids:
            material = manager.get_material(material_id)
            if material:
                materials.append(material)
            else:
                logger.warning(f"素材 {material_id} 不存在，已跳过")
        
        if not materials:
            return error_response("没有找到有效的素材")
        
        # 构建上下文
        context_parts = []
        for i, mat in enumerate(materials, 1):
            stage_name = {
                'analysis': '审题分析',
                'outline': '构思提纲',
                'essay': '写作辅助',
                'evaluation': '作文评估'
            }.get(mat['stage'], mat['stage'])
            
            context_parts.append(
                f"【{stage_name}】（题目：{mat['topic']}，模型：{mat['ai_model']}）\n"
                f"{mat['content']}"
            )
        
        full_context = "\n\n".join(context_parts)
        
        # 基于素材主题进行RAG检索，获取相关知识库内容
        rag_context = ""
        podcast_style_context = ""  # 播客风格参考
        try:
            from flask import current_app
            app_config = current_app.config.get('edurag', {})
            retriever = app_config.get('retriever')
            
            if retriever:
                # 提取所有素材的主题作为查询关键词
                topics = [mat['topic'] for mat in materials if mat.get('topic')]
                query = " ".join(topics[:3])  # 使用前3个主题作为查询
                
                logger.info(f"基于主题进行RAG检索: {query}")
                
                # 1. 检索相关知识库内容（chinese_essays）
                results = retriever.search(
                    query=query,
                    collection_name='chinese_essays',
                    top_k=5,
                    score_threshold=0.3
                )
                
                if results:
                    rag_parts = []
                    for i, result in enumerate(results, 1):
                        content = result.get('content', '')
                        if content and len(content) > 50:  # 过滤太短的内容
                            rag_parts.append(f"相关知识{i}: {content[:200]}...")
                    
                    if rag_parts:
                        rag_context = "\n\n".join(rag_parts)
                        logger.info(f"RAG检索到 {len(rag_parts)} 条相关知识")
                
                # 2. 检索历史播客文案（podcast_scripts），用于风格参考
                podcast_results = retriever.search(
                    query=query,
                    collection_name='podcast_scripts',
                    top_k=3,
                    score_threshold=0.2
                )
                
                if podcast_results:
                    podcast_parts = []
                    for i, result in enumerate(podcast_results, 1):
                        content = result.get('content', '')
                        metadata = result.get('metadata', {})
                        topic = metadata.get('topic', '未知主题')
                        if content and len(content) > 100:
                            podcast_parts.append(f"历史播客{i}（主题：{topic}）:\n{content[:300]}...")
                    
                    if podcast_parts:
                        podcast_style_context = "\n\n".join(podcast_parts)
                        logger.info(f"检索到 {len(podcast_parts)} 条历史播客风格参考")
        except Exception as e:
            logger.warning(f"RAG检索失败: {e}，将仅使用素材生成")
        
        # 使用共享的LLM实例（避免重复创建导致的内存泄漏）
        from flask import current_app
        app_config = current_app.config.get('edurag', {})
        llm = app_config.get('llm')
        
        if llm is None:
            logger.error("LLM实例未初始化")
            return error_response("服务端错误: LLM未初始化", 500)
        
        system_prompt = """你是一位专业的播客文案策划师，擅长将书面材料转化为生动有趣的播客对话。
你的任务是根据提供的素材，创作出：
1. 开场白自然亲切，吸引听众
2. 内容层次清晰，逻辑连贯
3. 语言口语化，适合听觉接收
4. 适当加入互动和过渡语
5. 结尾有总结或启发
6. 参考历史播客的风格和语气，保持一致性

请直接输出播客文案，不需要解释过程。"""
        
        # 构建 RAG 上下文部分
        rag_section = ""
        if rag_context:
            rag_section = f"以下是相关知识库内容（供参考）：\n\n{rag_context}\n\n"
        
        # 构建播客风格参考部分
        podcast_section = ""
        if podcast_style_context:
            podcast_section = f"以下是历史播客文案（请学习其风格和语气）：\n\n{podcast_style_context}\n\n"
        
        user_prompt = f"""{prompt}

以下是参考素材：

{full_context}

{rag_section}{podcast_section}请基于以上素材生成播客文案："""
        
        result = llm.generate(user_prompt, system_prompt=system_prompt, temperature=0.7)
        script_content = result.get('response', '')
        
        # 将生成的播客文案保存到播客知识库
        script_metadata = None
        try:
            from flask import current_app
            app_config = current_app.config.get('edurag', {})
            db = app_config.get('db')
            
            if db and script_content:
                # 提取主题作为元数据
                topics = [mat['topic'] for mat in materials if mat.get('topic')]
                main_topic = topics[0] if topics else '未命名'
                
                # 生成唯一ID和时间戳
                import time
                import uuid
                script_id = str(uuid.uuid4())
                timestamp = int(time.time() * 1000)
                
                # 确保集合存在（如果不存在则创建）
                if not db.collection_exists('podcast_scripts'):
                    logger.info("创建播客文案集合: podcast_scripts")
                    db.create_collection('podcast_scripts', metadata={'description': '播客文案知识库'})
                
                # 保存到播客知识库集合
                # 注意：ChromaDB 元数据必须是简单类型（str/int/float/bool），不能是 None 或 list
                db.add_documents(
                    collection_name='podcast_scripts',
                    documents=[script_content],
                    metadatas=[{
                        'script_id': script_id,
                        'version': 1,
                        'parent_id': '',  # ChromaDB 不支持 None，用空字符串代替
                        'title': f'{main_topic} - 播客文案 {time.strftime("%m-%d %H:%M")}',
                        'topic': main_topic,
                        'model': model,
                        'materials_count': len(materials),
                        'materials_ids': ','.join(material_ids) if material_ids else '',  # 列表转为字符串
                        'created_at': time.strftime('%Y-%m-%d %H:%M:%S'),
                        'updated_at': time.strftime('%Y-%m-%d %H:%M:%S'),
                        'status': 'draft',  # draft/completed/archived
                        'type': 'podcast_script',
                        'timestamp': timestamp  # 用于排序
                    }],
                    ids=[f'script_{script_id}']
                )
                logger.info(f"✅ 播客文案已保存到知识库: {script_id}")
                
                # 返回 script_id 给前端
                script_metadata = {
                    'script_id': script_id,
                    'version': 1,
                    'title': f'{main_topic} - 播客文案 {time.strftime("%m-%d %H:%M")}',
                    'created_at': time.strftime('%Y-%m-%d %H:%M:%S')
                }
        except Exception as e:
            logger.error(f"❌ 保存播客文案到知识库失败: {e}", exc_info=True)
            # 不设置 script_metadata，但不阻断流程
        
        # 更新素材状态为已导入
        for material_id in material_ids:
            manager.update_material_status(material_id, 'imported')
        
        return success_response({
            'script': script_content,
            'ai_model': model,
            'materials_count': len(materials),
            'script_metadata': script_metadata  # 返回文案元数据
        })
    
    except Exception as e:
        logger.error(f"生成播客文案失败: {e}")
        return error_response(f"服务端错误: {e}", 500)


@writing_bp.route('/podcast-tts', methods=['POST'])
def generate_podcast_tts():
    """
    将播客文案转换为语音（使用LongCat-AudioDiT）
    
    请求体（multipart/form-data）：
    - text: 要转换的文本
    - ref_audio: 参考音频文件（可以是文件或已上传的文件路径）
    - prompt_text: 参考音频对应的文本
    - model: 模型名称（可选，默认 qwen3:8b）
    - nfe: ODE步数（可选，默认 18）
    - guidance_strength: 引导强度（可选，默认 3.5）
    
    响应体：
    {
        "success": true,
        "audio_url": "/data/podcast_audio/podcast_xxx.wav",
        "duration_sec": 45.2
    }
    """
    try:
        # 获取表单数据
        text = request.form.get('text')
        prompt_text = request.form.get('prompt_text', '')  # 允许为空，稍后从JSON读取
        nfe = int(request.form.get('nfe', 18))
        guidance_strength = float(request.form.get('guidance_strength', 3.5))
        
        if not text:
            return error_response("必须提供 text 字段")
        
        # 获取参考音频文件或路径
        ref_audio_path = None
        
        # 检查是否是已保存的音频文件路径
        saved_audio_id = request.form.get('ref_audio_id')
        if saved_audio_id:
            import os
            from flask import current_app
            app_config = current_app.config.get('edurag', {})
            upload_dir = app_config.get('upload_dir', './uploads')
            ref_audio_dir = os.path.join(upload_dir, 'podcast_ref_audios')
            saved_path = os.path.join(ref_audio_dir, saved_audio_id)
            
            # 如果直接路径不存在，尝试添加常见音频扩展名
            if not os.path.exists(saved_path):
                for ext in ['.mp3', '.wav', '.m4a', '.flac']:
                    test_path = saved_path + ext
                    if os.path.exists(test_path):
                        saved_path = test_path
                        saved_audio_id = saved_audio_id + ext
                        logger.info(f"自动匹配到音频文件: {saved_audio_id}")
                        break
            
            if os.path.exists(saved_path):
                ref_audio_path = Path(saved_path)
                logger.info(f"使用已保存的参考音频: {saved_audio_id}")
                
                # 自动从JSON元数据文件中读取 prompt_text（如果前端没有提供）
                if not prompt_text:
                    audio_id = os.path.splitext(saved_audio_id)[0]
                    metadata_filepath = os.path.join(ref_audio_dir, f"{audio_id}.json")
                    if os.path.exists(metadata_filepath):
                        try:
                            import json
                            with open(metadata_filepath, 'r', encoding='utf-8') as f:
                                metadata = json.load(f)
                                prompt_text = metadata.get('prompt_text', '')
                                logger.info(f"从元数据文件读取到 prompt_text: {prompt_text}")
                        except Exception as e:
                            logger.warning(f"读取元数据文件失败: {e}")
            else:
                return error_response(f"参考音频不存在: {saved_audio_id}", 404)
        elif 'ref_audio' in request.files:
            # 上传新的参考音频
            ref_audio_file = request.files['ref_audio']
            if ref_audio_file.filename == '':
                return error_response("参考音频文件名为空")
            
            # 保存到临时目录
            import tempfile
            temp_dir = Path(tempfile.mkdtemp())
            ref_audio_path = temp_dir / f"ref_{ref_audio_file.filename}"
            ref_audio_file.save(str(ref_audio_path))
            logger.info(f"上传新的参考音频: {ref_audio_file.filename}")
        else:
            return error_response("必须上传 ref_audio 文件或提供 ref_audio_id")
        
        # 最终验证：如果还是没有 prompt_text，报错
        if not prompt_text:
            return error_response("必须提供 prompt_text 字段，或确保已保存的音频包含对应的文本")
        
        logger.info(f"收到TTS请求: 文本长度={len(text)}, 参考音频={ref_audio_path}, prompt_text={prompt_text}")
        
        # 调用TTS生成器
        from podcast.tts_generator import get_tts_generator
        tts_generator = get_tts_generator()
        
        output_filename = f"podcast_{int(time.time()*1000)}.wav"
        audio_path = tts_generator.generate_speech(
            text=text,
            ref_audio_path=str(ref_audio_path),
            prompt_text=prompt_text,
            output_filename=output_filename,
            nfe=nfe,
            guidance_strength=guidance_strength,
        )
        
        # 计算音频时长
        import soundfile as sf
        data, sr = sf.read(audio_path)
        duration_sec = len(data) / sr
        
        # 清理临时文件（仅当上传了新音频时才需要清理）
        import shutil
        if 'temp_dir' in dir() and temp_dir is not None:
            shutil.rmtree(temp_dir, ignore_errors=True)
        
        # 返回相对路径（用于前端访问）
        audio_url = f"/podcast-audio/{Path(audio_path).name}"
        
        return success_response({
            'audio_url': audio_url,
            'duration_sec': round(duration_sec, 2),
            'message': '语音生成成功'
        })
    
    except FileNotFoundError as e:
        logger.error(f"LongCat项目文件缺失: {e}")
        return error_response(f"LongCat-AudioDiT 未正确配置: {e}", 500)
    except Exception as e:
        logger.error(f"TTS生成失败: {e}", exc_info=True)
        return error_response(f"服务端错误: {e}", 500)


@writing_bp.route('/podcast-ref-audios', methods=['GET'])
def get_podcast_ref_audios():
    """
    获取已保存的参考音频列表（包含元数据）
    
    返回：
    - audios: 音频列表，每个包含 id, name, path, prompt_text, created_at
    """
    try:
        import os
        import json
        from flask import current_app
        
        app_config = current_app.config.get('edurag', {})
        upload_dir = app_config.get('upload_dir', './uploads')
        ref_audio_dir = os.path.join(upload_dir, 'podcast_ref_audios')
        
        if not os.path.exists(ref_audio_dir):
            return success_response({'audios': []})
        
        # 扫描目录下的所有音频文件
        audios = []
        for filename in os.listdir(ref_audio_dir):
            if filename.endswith(('.wav', '.mp3', '.m4a', '.flac')):
                filepath = os.path.join(ref_audio_dir, filename)
                stat = os.stat(filepath)
                
                # 提取ID并查找对应的元数据文件
                audio_id = os.path.splitext(filename)[0]
                metadata_file = os.path.join(ref_audio_dir, f"{audio_id}.json")
                
                prompt_text = ''
                original_filename = filename
                
                # 如果有元数据文件，读取其中的文本
                if os.path.exists(metadata_file):
                    try:
                        with open(metadata_file, 'r', encoding='utf-8') as f:
                            metadata = json.load(f)
                            prompt_text = metadata.get('prompt_text', '')
                            original_filename = metadata.get('original_filename', filename)
                    except Exception as e:
                        logger.warning(f"读取元数据失败 {metadata_file}: {e}")
                
                audios.append({
                    'id': audio_id,
                    'name': original_filename,
                    'path': filepath,
                    'size': stat.st_size,
                    'created_at': stat.st_ctime,
                    'prompt_text': prompt_text
                })
        
        # 按创建时间降序排序
        audios.sort(key=lambda x: x['created_at'], reverse=True)
        
        logger.info(f"获取到 {len(audios)} 个参考音频")
        return success_response({'audios': audios})
    
    except Exception as e:
        logger.error(f"获取参考音频列表失败: {e}")
        return error_response(f"服务端错误: {e}", 500)


@writing_bp.route('/podcast-ref-audios/upload', methods=['POST'])
def upload_podcast_ref_audio():
    """
    上传并保存参考音频及其对应的文本
    
    请求体（multipart/form-data）：
    - ref_audio: 音频文件
    - prompt_text: 音频对应的文本（可选）
    """
    try:
        import os
        import json
        import time
        import uuid
        from flask import current_app
        
        if 'ref_audio' not in request.files:
            return error_response("必须上传 ref_audio 文件", 400)
        
        ref_audio_file = request.files['ref_audio']
        if ref_audio_file.filename == '':
            return error_response("参考音频文件名为空", 400)
        
        # 获取音频对应的文本
        prompt_text = request.form.get('prompt_text', '')
        
        app_config = current_app.config.get('edurag', {})
        upload_dir = app_config.get('upload_dir', './uploads')
        ref_audio_dir = os.path.join(upload_dir, 'podcast_ref_audios')
        
        # 确保目录存在
        os.makedirs(ref_audio_dir, exist_ok=True)
        
        # 生成唯一文件名
        ext = os.path.splitext(ref_audio_file.filename)[1]
        unique_id = f"{uuid.uuid4().hex}_{int(time.time())}"
        audio_filename = f"{unique_id}{ext}"
        metadata_filename = f"{unique_id}.json"
        
        audio_filepath = os.path.join(ref_audio_dir, audio_filename)
        metadata_filepath = os.path.join(ref_audio_dir, metadata_filename)
        
        # 保存音频文件
        ref_audio_file.save(audio_filepath)
        
        # 保存元数据（包含文本）
        metadata = {
            'id': unique_id,
            'audio_file': audio_filename,
            'prompt_text': prompt_text,
            'original_filename': ref_audio_file.filename,
            'created_at': time.strftime('%Y-%m-%d %H:%M:%S'),
            'timestamp': int(time.time()),
            'size': os.path.getsize(audio_filepath)
        }
        
        with open(metadata_filepath, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        logger.info(f"参考音频已保存: {audio_filename}, 文本长度: {len(prompt_text)}")
        
        return success_response({
            'id': unique_id,
            'name': audio_filename,
            'path': audio_filepath,
            'prompt_text': prompt_text,
            'message': '参考音频及文本已保存'
        })
    
    except Exception as e:
        logger.error(f"上传参考音频失败: {e}")
        return error_response(f"服务端错误: {e}", 500)


@writing_bp.route('/podcast-ref-audios/<audio_id>/text', methods=['PUT'])
def update_podcast_ref_audio_text(audio_id: str):
    """
    更新指定参考音频的文本
    
    请求体：
    - prompt_text: 新的文本内容
    """
    try:
        import os
        import json
        from flask import current_app, request
        
        app_config = current_app.config.get('edurag', {})
        upload_dir = app_config.get('upload_dir', './uploads')
        ref_audio_dir = os.path.join(upload_dir, 'podcast_ref_audios')
        
        # 查找音频文件
        audio_filepath = None
        for ext in ['.mp3', '.wav', '.m4a', '.flac']:
            test_path = os.path.join(ref_audio_dir, f"{audio_id}{ext}")
            if os.path.exists(test_path):
                audio_filepath = test_path
                break
        
        if not audio_filepath:
            return error_response(f"音频文件不存在: {audio_id}", 404)
        
        # 获取新的文本
        data = request.get_json()
        prompt_text = data.get('prompt_text', '')
        
        # 更新元数据文件
        metadata_filepath = os.path.join(ref_audio_dir, f"{audio_id}.json")
        if os.path.exists(metadata_filepath):
            with open(metadata_filepath, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            metadata['prompt_text'] = prompt_text
            
            with open(metadata_filepath, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            
            logger.info(f"已更新参考音频文本: {audio_id}, 文本长度: {len(prompt_text)}")
        else:
            # 如果没有元数据文件，创建一个
            metadata = {
                'id': audio_id,
                'audio_file': os.path.basename(audio_filepath),
                'prompt_text': prompt_text,
                'original_filename': os.path.basename(audio_filepath),
                'created_at': '',
                'timestamp': 0,
                'size': os.path.getsize(audio_filepath)
            }
            
            with open(metadata_filepath, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            
            logger.info(f"已创建元数据文件: {audio_id}")
        
        return success_response({'message': '文本已更新'})
    
    except Exception as e:
        logger.error(f"更新参考音频文本失败: {e}")
        return error_response(f"服务端错误: {e}", 500)


@writing_bp.route('/podcast-ref-audios/<filename>', methods=['DELETE'])
def delete_podcast_ref_audio(filename: str):
    """
    删除指定的参考音频及其元数据
    
    参数 filename 可以是：
    - 完整文件名（带扩展名）：2014b9ba6a9d4535bc3fdb721e066140_1782071410.mp3
    - ID（不带扩展名）：2014b9ba6a9d4535bc3fdb721e066140_1782071410
    """
    try:
        import os
        from flask import current_app
        
        app_config = current_app.config.get('edurag', {})
        upload_dir = app_config.get('upload_dir', './uploads')
        ref_audio_dir = os.path.join(upload_dir, 'podcast_ref_audios')
        
        # 如果传入的是ID（不带扩展名），自动添加 .mp3 扩展名
        if not filename.endswith(('.mp3', '.wav', '.m4a', '.flac')):
            # 尝试查找对应的音频文件
            audio_filepath = None
            for ext in ['.mp3', '.wav', '.m4a', '.flac']:
                test_path = os.path.join(ref_audio_dir, f"{filename}{ext}")
                if os.path.exists(test_path):
                    audio_filepath = test_path
                    filename = f"{filename}{ext}"
                    break
            
            if not audio_filepath:
                return error_response(f"音频文件不存在: {filename}", 404)
        else:
            audio_filepath = os.path.join(ref_audio_dir, filename)
            if not os.path.exists(audio_filepath):
                return error_response(f"音频文件不存在: {filename}", 404)
        
        # 删除音频文件
        os.remove(audio_filepath)
        
        # 删除元数据文件（如果存在）
        audio_id = os.path.splitext(filename)[0]
        metadata_filepath = os.path.join(ref_audio_dir, f"{audio_id}.json")
        if os.path.exists(metadata_filepath):
            os.remove(metadata_filepath)
            logger.info(f"已删除参考音频及元数据: {filename}")
        else:
            logger.info(f"已删除参考音频: {filename}")
        
        return success_response({'message': f'已删除: {filename}'})
    
    except Exception as e:
        logger.error(f"删除参考音频失败: {e}")
        return error_response(f"服务端错误: {e}", 500)


@writing_bp.route('/podcast-materials/<material_id>/add-to-rag', methods=['POST'])
def add_podcast_material_to_rag(material_id: str):
    """
    将播客素材/文案添加到RAG知识库
    
    请求体（可选）：
    {
        "content": "要存入的内容（可选，默认使用素材内容）",
        "title": "标题（可选，默认自动生成）"
    }
    
    响应体：
    {
        "success": true,
        "message": "已存入RAG知识库",
        "chunk_count": 3
    }
    """
    try:
        data = request.get_json() or {}
        
        # 获取素材或文案内容
        manager = get_podcast_manager()
        material = manager.get_material(material_id)
        
        if not material:
            # 尝试从文案数据库查找
            script_mgr = None
            from podcast.script_manager import PodcastScriptManager
            script_mgr = PodcastScriptManager()
            script = script_mgr.get_script(material_id)
            if script:
                content = script.get('content', '')
                title = script.get('title', f'播客文案_{material_id}')
                topic = script.get('topic', '未知主题')
            else:
                return error_response(f"素材或文案不存在: {material_id}", 404)
        else:
            content = data.get('content', material.get('content', ''))
            topic = material.get('topic', '未知主题')
            title = data.get('title', f"播客素材_{material_id}")
        
        if not content:
            return error_response("内容为空，无法存入RAG")
        
        # 初始化RAG数据库
        db = EduRAGDatabase()
        collection_name = 'chinese_essays'
        
        # 确保集合存在
        if collection_name not in [c.name for c in db.client.list_collections()]:
            db.create_collection(collection_name)
        
        collection = db.get_collection(collection_name)
        
        # 按段落分块（每段作为一个chunk）
        chunks = [chunk.strip() for chunk in content.split('\n\n') if len(chunk.strip()) > 20]
        
        if not chunks:
            # 如果没有段落分隔，按句子分割
            chunks = [chunk.strip() for chunk in content.split('。') if len(chunk.strip()) > 10]
        
        if not chunks:
            return error_response("内容格式不正确，无法分块")
        
        # 生成IDs和元数据
        import hashlib
        import time
        chunk_ids = []
        metadatas = []
        
        for i, chunk in enumerate(chunks):
            # 生成唯一ID
            chunk_hash = hashlib.md5(f"{material_id}_{i}_{time.time()}".encode()).hexdigest()
            chunk_id = f"podcast_{chunk_hash}"
            chunk_ids.append(chunk_id)
            
            # 构建元数据
            metadata = {
                'source_type': 'podcast_script',  # 标识为播客文案来源
                'material_id': material_id,
                'topic': topic,
                'title': title,
                'chunk_index': i,
                'total_chunks': len(chunks),
                'created_at': int(time.time())
            }
            metadatas.append(metadata)
        
        # 生成embeddings
        embeddings = db.embedder.encode(chunks)
        
        # 添加到ChromaDB
        collection.add(
            ids=chunk_ids,
            embeddings=embeddings,
            documents=chunks,
            metadatas=metadatas
        )
        
        # 更新素材状态（如果存在）
        if material:
            material['in_rag'] = True
            material['rag_added_at'] = time.strftime('%Y-%m-%dT%H:%M:%S')
            file_path = manager.storage_path / f"{material_id}.json"
            import json
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(material, f, ensure_ascii=False, indent=2)
        
        logger.info(f"✅ 播客素材已存入RAG: {material_id}, {len(chunks)}个chunks")
        
        return success_response({
            'message': '已存入RAG知识库',
            'chunk_count': len(chunks),
            'collection': collection_name
        })
    
    except Exception as e:
        logger.error(f"存入RAG失败: {e}", exc_info=True)
        return error_response(f"服务端错误: {e}", 500)


@writing_bp.route('/podcast-scripts/rss', methods=['GET'])
def generate_podcast_rss_feed():
    """
    生成播客文案的RSS 2.0 Feed（含iTunes扩展）
    
    查询参数：
    - stage: 阶段过滤（shenti/gousi/xiezuo/pinggu，可选，不传则生成所有阶段的混合feed）
    - script_ids: 逗号分隔的文案ID列表（可选，默认包含所有completed状态的文案）
    - topic: 主题过滤（可选）
    - limit: 数量限制（默认50）
    
    响应体：
    {
        "success": true,
        "rss_xml": "<?xml version='1.0' encoding='UTF-8'?><rss version='2.0'...",
        "download_url": "/api/writing/podcast-scripts/rss/download?token=xxx",
        "stage": "shenti"  // 如果指定了stage参数
    }
    """
    try:
        from flask import current_app
        from podcast.script_state_manager import get_script_state_manager
        app_config = current_app.config.get('edurag', {})
        db = app_config.get('db')
        
        if not db:
            return error_response("数据库未初始化", 500)
        
        # 获取查询参数
        stage = request.args.get('stage')  # 新增stage参数
        script_ids_param = request.args.get('script_ids')
        topic = request.args.get('topic')
        limit = int(request.args.get('limit', 50))
        
        # 验证stage参数
        valid_stages = ['shenti', 'gousi', 'xiezuo', 'pinggu']
        if stage and stage not in valid_stages:
            return error_response(f"无效的stage值: {stage}，必须是 {valid_stages} 之一", 400)
        
        # 检查集合是否存在
        if not db.collection_exists('podcast_scripts'):
            return error_response("播客文案集合尚未创建", 404)
        
        collection = db.get_collection('podcast_scripts')
        
        # 从状态管理器获取所有 completed 状态的文案ID
        state_mgr = get_script_state_manager()
        all_states = state_mgr.get_all_states()
        completed_script_ids = [
            sid for sid, state in all_states.items() 
            if state.get('status') == 'completed'
        ]
        
        # 如果指定了stage，进一步过滤
        if stage:
            completed_script_ids = [
                sid for sid in completed_script_ids
                if all_states.get(sid, {}).get('stage') == stage
            ]
            logger.info(f"✅ 阶段过滤: {stage}, 找到 {len(completed_script_ids)} 个completed文案")
        
        # 构建where条件
        where_conditions = [{'type': 'podcast_script'}]
        
        if not completed_script_ids:
            # 如果没有 completed 的文案，返回空
            return error_response("没有找到状态为 completed 的播客文案", 404)
        elif len(completed_script_ids) == 1:
            # 如果只有一个 completed 文案，直接使用 script_id 过滤（避免 $or 单元素问题）
            where_conditions.append({'script_id': completed_script_ids[0]})
        else:
            # 多个 completed 文案，使用 $or
            where_conditions.append({
                '$or': [{'script_id': sid} for sid in completed_script_ids]
            })
        
        if topic:
            where_conditions.append({'topic': topic})
        
        where_filter = {'$and': where_conditions}
        
        results = collection.get(
            where=where_filter,
            limit=limit,
            include=['metadatas', 'documents']
        )
        
        if not results['metadatas']:
            return error_response("没有找到符合条件的播客文案", 404)
        
        # 如果指定了script_ids，进行过滤
        if script_ids_param:
            requested_ids = [sid.strip() for sid in script_ids_param.split(',')]
            filtered_results = []
            for metadata, document in zip(results['metadatas'], results['documents']):
                if metadata.get('script_id') in requested_ids:
                    filtered_results.append((metadata, document))
            results_list = filtered_results
        else:
            results_list = list(zip(results['metadatas'], results['documents']))
        
        if not results_list:
            return error_response("没有找到指定的播客文案", 404)
        
        # 生成RSS XML
        rss_xml = _generate_rss_xml(results_list)
        
        # 生成临时下载链接（使用token）
        import hashlib
        import time
        token = hashlib.md5(f"{time.time()}_{len(rss_xml)}".encode()).hexdigest()
        
        # 缓存RSS内容（5分钟过期）- Redis可选
        cache_key = f"rss_cache_{token}"
        try:
            import redis
            r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
            r.setex(cache_key, 300, rss_xml)  # 5分钟过期
        except ImportError:
            # Redis未安装，跳过缓存
            logger.debug("Redis未安装，RSS内容将不进行缓存")
        except Exception as e:
            logger.warning(f"Redis不可用: {e}，RSS内容将不进行缓存")
        
        logger.info(f"✅ RSS Feed已生成，包含 {len(results_list)} 个文案")
        
        response_data = {
            'rss_xml': rss_xml,
            'download_url': f'/api/writing/podcast-scripts/rss/download?token={token}',
            'count': len(results_list)
        }
        
        # 如果指定了stage，返回stage信息
        if stage:
            response_data['stage'] = stage
        
        return success_response(response_data)
    
    except Exception as e:
        logger.error(f"生成RSS Feed失败: {e}", exc_info=True)
        return error_response(f"服务端错误: {e}", 500)


@writing_bp.route('/podcast-scripts/rss/download', methods=['GET'])
def download_podcast_rss():
    """
    下载RSS Feed XML文件
    
    查询参数：
    - token: 下载令牌（从generate_podcast_rss_feed接口获取）
    
    响应：直接返回XML文件下载
    """
    try:
        from flask import make_response
        token = request.args.get('token')
        
        if not token:
            return error_response("缺少token参数", 400)
        
        # 从缓存中获取RSS内容
        import redis
        rss_xml = None
        try:
            r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
            cache_key = f"rss_cache_{token}"
            rss_xml = r.get(cache_key)
        except:
            logger.warning("Redis不可用，无法获取缓存的RSS内容")
        
        if not rss_xml:
            return error_response("RSS内容不存在或已过期，请重新生成", 404)
        
        # 返回XML文件
        response = make_response(rss_xml)
        response.headers['Content-Type'] = 'application/xml; charset=utf-8'
        response.headers['Content-Disposition'] = f'attachment; filename="podcast_feed_{token[:8]}.xml"'
        
        return response
    
    except Exception as e:
        logger.error(f"下载RSS Feed失败: {e}", exc_info=True)
        return error_response(f"服务端错误: {e}", 500)


def _generate_rss_xml(script_list):
    """
    生成符合RSS 2.0 + iTunes播客扩展标准的XML
    
    参数：
    script_list: [(metadata, document), ...] 元组列表
    
    返回：
    str: RSS XML字符串
    """
    from datetime import datetime
    import html
    
    # RSS头部
    rss_header = '''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>30分钟作文实战</title>
    <link>https://dee422.github.io</link>
    <description>《30分钟作文实战》是一档面向高中生的作文训练播客。依托EduRAG AI作文训练系统，从审题分析、构思提纲、写作辅助到写作评估，帮助害怕写作文的学生建立系统化写作方法，通过短期强化训练，实现30分钟完成高质量考场作文的目标。</description>
    <language>zh-cn</language>
    <itunes:author>EduRAG团队</itunes:author>
    <itunes:summary>《30分钟作文实战》是一档面向高中生的作文训练播客。依托EduRAG AI作文训练系统，从审题分析、构思提纲、写作辅助到写作评估，帮助害怕写作文的学生建立系统化写作方法，通过短期强化训练，实现30分钟完成高质量考场作文的目标。</itunes:summary>
    <itunes:explicit>no</itunes:explicit>
    <itunes:image href="https://edurang.example.com/podcast-cover.png"/>
    <itunes:category text="Education">
      <itunes:category text="Language Learning"/>
    </itunes:category>
'''
    
    # 生成每个文案的item
    items_xml = ''
    for metadata, content in script_list:
        script_id = metadata.get('script_id', '')
        title = html.escape(metadata.get('title', '未命名'))
        topic = html.escape(metadata.get('topic', '未知'))
        created_at = metadata.get('created_at', '')
        model = metadata.get('model', 'unknown')
        
        # 格式化发布日期（RFC 2822）
        pub_date = _format_rfc2822_date(created_at)
        
        # 生成音频URL（假设有TTS服务）
        # 注意：实际使用时需要替换为真实的音频URL
        audio_url = f"https://edurang.example.com/audio/{script_id}.mp3"
        
        # 计算时长（估算：每分钟约250字）
        word_count = len(content) if content else 0
        duration_minutes = max(1, word_count // 250)
        duration_str = f"00:{duration_minutes:02d}:00"
        
        # 清理内容，去除多余空白和特殊字符
        clean_content = html.escape(content[:4000]) if content else ''  # iTunes要求description不超过4000字符
        
        item_xml = f'''    <item>
      <title>{title}</title>
      <description>{clean_content}</description>
      <link>https://edurang.example.com/podcast/{script_id}</link>
      <guid isPermaLink="true">{script_id}</guid>
      <pubDate>{pub_date}</pubDate>
      <enclosure url="{audio_url}" length="0" type="audio/mpeg"/>
      <itunes:author>EduRAG AI</itunes:author>
      <itunes:subtitle>{topic}</itunes:subtitle>
      <itunes:summary>{clean_content}</itunes:summary>
      <itunes:explicit>no</itunes:explicit>
      <itunes:duration>{duration_str}</itunes:duration>
      <itunes:episodeType>full</itunes:episodeType>
    </item>
'''
        items_xml += item_xml
    
    # RSS尾部
    rss_footer = '''  </channel>
</rss>'''
    
    return rss_header + items_xml + rss_footer


def _format_rfc2822_date(date_str):
    """
    将日期字符串转换为RFC 2822格式
    
    参数：
    date_str: 日期字符串（ISO格式或时间戳）
    
    返回：
    str: RFC 2822格式的日期字符串
    """
    from datetime import datetime
    import email.utils
    
    try:
        if date_str:
            # 尝试解析ISO格式日期
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        else:
            dt = datetime.now()
        
        # 转换为RFC 2822格式
        return email.utils.format_datetime(dt)
    except:
        # 失败时返回当前时间
        return email.utils.format_datetime(datetime.now())


@writing_bp.route('/podcast-scripts/<script_id>/status', methods=['PUT'])
def update_podcast_script_status(script_id: str):
    """
    更新播客文案的状态（draft/completed/archived）
    
    路径参数：
    - script_id: 文案ID
    
    请求体：
    {
        "status": "completed"  // draft, completed, 或 archived
    }
    
    响应体：
    {
        "success": true,
        "message": "状态已更新",
        "new_status": "completed"
    }
    """
    try:
        from podcast.script_state_manager import get_script_state_manager
        
        # 获取新状态
        data = request.get_json()
        new_status = data.get('status')
        
        if new_status not in ['draft', 'completed', 'archived']:
            return error_response(f"无效的状态值: {new_status}，必须是 draft/completed/archived 之一", 400)
        
        # 使用JSON文件管理状态，避免ChromaDB更新问题
        state_mgr = get_script_state_manager()
        state_mgr.update_script_status(script_id, new_status)
        
        logger.info(f"✅ 播客文案状态已更新: {script_id} -> {new_status}")
        
        return success_response({
            'message': '状态已更新',
            'new_status': new_status,
            'script_id': script_id
        })
    
    except Exception as e:
        logger.error(f"更新文案状态失败: {e}", exc_info=True)
        return error_response(f"服务端错误: {e}", 500)


@writing_bp.route('/podcast-scripts/<script_id>/stage', methods=['PUT'])
def update_podcast_script_stage(script_id: str):
    """
    更新播客文案所属阶段
    
    路径参数：
    - script_id: 文案ID
    
    请求体：
    {
        "stage": "shenti"  // shenti/gousi/xiezuo/pinggu
    }
    
    响应体：
    {
        "success": true,
        "message": "阶段已更新",
        "new_stage": "shenti"
    }
    """
    try:
        from podcast.script_state_manager import get_script_state_manager
        
        # 获取新阶段
        data = request.get_json()
        new_stage = data.get('stage')
        
        if new_stage not in ['shenti', 'gousi', 'xiezuo', 'pinggu']:
            return error_response(f"无效的阶段值: {new_stage}，必须是 shenti/gousi/xiezuo/pinggu 之一", 400)
        
        # 使用JSON文件管理阶段
        state_mgr = get_script_state_manager()
        success = state_mgr.update_script_stage(script_id, new_stage)
        
        if not success:
            return error_response("更新阶段失败", 500)
        
        logger.info(f"✅ 播客文案阶段已更新: {script_id} -> {new_stage}")
        
        return success_response({
            'message': '阶段已更新',
            'new_stage': new_stage,
            'script_id': script_id
        })
    
    except Exception as e:
        logger.error(f"更新文案阶段失败: {e}", exc_info=True)
        return error_response(f"服务端错误: {e}", 500)


@writing_bp.route('/podcast-scripts/<script_id>/audio-association', methods=['POST'])
def add_audio_association(script_id: str):
    """
    为播客文案添加音频关联
    
    请求体:
    {
        "audio_id": "音频文件ID"
    }
    """
    try:
        from podcast.script_state_manager import get_script_state_manager
        
        data = request.get_json()
        audio_id = data.get('audio_id')
        
        if not audio_id:
            return error_response("缺少audio_id参数", 400)
        
        state_mgr = get_script_state_manager()
        state_mgr.add_audio_association(script_id, audio_id)
        
        return success_response({
            'message': '音频关联已添加',
            'script_id': script_id,
            'audio_id': audio_id
        })
    
    except Exception as e:
        logger.error(f"添加音频关联失败: {e}", exc_info=True)
        return error_response(f"服务端错误: {e}", 500)


@writing_bp.route('/podcast-scripts/<script_id>/audio-association', methods=['DELETE'])
def remove_audio_association(script_id: str):
    """
    移除播客文案的音频关联
    
    请求体:
    {
        "audio_id": "音频文件ID"
    }
    """
    try:
        from podcast.script_state_manager import get_script_state_manager
        
        data = request.get_json()
        audio_id = data.get('audio_id')
        
        if not audio_id:
            return error_response("缺少audio_id参数", 400)
        
        state_mgr = get_script_state_manager()
        state_mgr.remove_audio_association(script_id, audio_id)
        
        return success_response({
            'message': '音频关联已移除',
            'script_id': script_id,
            'audio_id': audio_id
        })
    
    except Exception as e:
        logger.error(f"移除音频关联失败: {e}", exc_info=True)
        return error_response(f"服务端错误: {e}", 500)


@writing_bp.route('/podcast-scripts/<script_id>/audio-files', methods=['GET'])
def get_script_audio_files(script_id: str):
    """
    获取播客文案关联的音频文件列表
    """
    try:
        from podcast.script_state_manager import get_script_state_manager
        
        state_mgr = get_script_state_manager()
        audio_ids = state_mgr.get_script_audio_files(script_id)
        
        # 从数据库获取音频文件详细信息
        app_config = current_app.config.get('edurag', {})
        db = app_config.get('db')
        
        if not db or not db.collection_exists('podcast_ref_audios'):
            return success_response({'audio_files': []})
        
        collection = db.get_collection('podcast_ref_audios')
        
        if not audio_ids:
            return success_response({'audio_files': []})
        elif len(audio_ids) == 1:
            where_filter = {'$and': [{'type': 'ref_audio'}, {'audio_id': audio_ids[0]}]}
        else:
            where_filter = {
                '$and': [
                    {'type': 'ref_audio'},
                    {'$or': [{'audio_id': aid} for aid in audio_ids]}
                ]
            }
        
        results = collection.get(
            where=where_filter,
            include=['metadatas']
        )
        
        audio_files = []
        for metadata in results['metadatas']:
            audio_files.append({
                'audio_id': metadata.get('audio_id'),
                'filename': metadata.get('filename'),
                'duration': metadata.get('duration'),
                'file_size': metadata.get('file_size'),
                'created_at': metadata.get('created_at')
            })
        
        return success_response({'audio_files': audio_files})
    
    except Exception as e:
        logger.error(f"获取音频文件列表失败: {e}", exc_info=True)
        return error_response(f"服务端错误: {e}", 500)


# ─────────────────────────────────────────────────────────
# POST /writing/search-quotes  名人名言检索
# ─────────────────────────────────────────────────────────
@writing_bp.route('/search-quotes', methods=['POST'])
def search_quotes():
    """
    基于RAG知识库检索名人名言
    
    请求体：
    {
        "topic": "主题关键词（必填）",
        "top_k": "返回数量（可选，默认10）"
    }
    
    响应体：
    {
        "success": true,
        "quotes": [
            {
                "content": "名言内容",
                "author": "作者",
                "source": "出处",
                "metadata": {...}
            }
        ],
        "count": 数量
    }
    """
    data = request.get_json()
    if not data:
        return error_response("请求体不能为空")
    
    topic = data.get('topic')
    if not topic:
        return error_response("必须提供 topic 字段")
    
    top_k = data.get('top_k', 10)
    
    try:
        retriever = current_app.config['edurag']['retriever']
        
        # 构建查询：搜索包含“名言”、“警句”等关键词的内容
        query = f"{topic} 名言 警句 格言"
        
        results = retriever.search(
            collection_name='chinese_essays',
            query=query,
            top_k=top_k * 2,  # 多检索一些，后续过滤
            score_threshold=0.1
        )
        
        # 过滤和提取名言
        quotes = []
        for i, (doc, meta) in enumerate(zip(results.documents, results.metadatas)):
            # 简单启发式：短文本更可能是名言
            if len(doc) < 300 and any(keyword in doc for keyword in ['曰', '云', '说', '言', '谓']):
                # 尝试提取作者信息
                author = meta.get('author', '佚名')
                source = meta.get('source', meta.get('source_file', '未知'))
                
                quotes.append({
                    'id': f'quote_{i}',
                    'content': doc.strip(),
                    'author': author,
                    'source': source,
                    'score': round(results.scores[i], 3),
                    'metadata': meta
                })
        
        # 按相似度排序，取前top_k个
        quotes.sort(key=lambda x: x['score'], reverse=True)
        quotes = quotes[:top_k]
        
        logger.info(f"检索到 {len(quotes)} 条相关名言")
        
        return success_response({
            'quotes': quotes,
            'count': len(quotes)
        })
    
    except Exception as e:
        logger.error(f"名言检索失败: {e}")
        return error_response(f"服务端错误: {e}", 500)


# ─────────────────────────────────────────────────────────
# POST /writing/search-materials  真实案例检索
# ─────────────────────────────────────────────────────────
@writing_bp.route('/search-materials', methods=['POST'])
def search_materials():
    """
    基于RAG知识库检索真实案例、历史事件
    
    请求体：
    {
        "topic": "主题关键词（必填）",
        "top_k": "返回数量（可选，默认10）"
    }
    
    响应体：
    {
        "success": true,
        "materials": [
            {
                "title": "案例标题",
                "content": "案例内容",
                "type": "案例类型（历史事件/现实案例/人物故事）",
                "metadata": {...}
            }
        ],
        "count": 数量
    }
    """
    data = request.get_json()
    if not data:
        return error_response("请求体不能为空")
    
    topic = data.get('topic')
    if not topic:
        return error_response("必须提供 topic 字段")
    
    top_k = data.get('top_k', 10)
    
    try:
        retriever = current_app.config['edurag']['retriever']
        
        # 构建查询：搜索包含“案例”、“事件”、“故事”等关键词的内容
        query = f"{topic} 案例 事例 故事 历史 事件 实例"
        
        results = retriever.search(
            collection_name='chinese_essays',
            query=query,
            top_k=top_k * 2,
            score_threshold=0.1
        )
        
        # 过滤和提取案例
        materials = []
        for i, (doc, meta) in enumerate(zip(results.documents, results.metadatas)):
            # 中等长度的文本更适合作为案例
            if 100 < len(doc) < 1000:
                # 判断案例类型
                case_type = "现实案例"
                if any(kw in doc for kw in ['历史', '古代', '唐朝', '宋朝', '明朝', '清朝']):
                    case_type = "历史事件"
                elif any(kw in doc for kw in ['人物', '故事', '事迹']):
                    case_type = "人物故事"
                
                materials.append({
                    'id': f'material_{i}',
                    'title': meta.get('topic', f'{topic}相关案例'),
                    'content': doc.strip(),
                    'type': case_type,
                    'score': round(results.scores[i], 3),
                    'metadata': meta
                })
        
        # 按相似度排序，取前top_k个
        materials.sort(key=lambda x: x['score'], reverse=True)
        materials = materials[:top_k]
        
        logger.info(f"检索到 {len(materials)} 条相关案例")
        
        return success_response({
            'materials': materials,
            'count': len(materials)
        })
    
    except Exception as e:
        logger.error(f"案例检索失败: {e}")
        return error_response(f"服务端错误: {e}", 500)


# ─────────────────────────────────────────────────────────
# PUT /writing/quotes-materials/<id>  更新名言或案例
# ─────────────────────────────────────────────────────────
@writing_bp.route('/quotes-materials/<item_id>', methods=['PUT'])
def update_quote_or_material(item_id):
    """
    更新名言或案例内容
    
    请求体：
    {
        "type": "quote" | "material",
        "content": "新内容",
        "author": "作者(仅名言)",
        "source": "出处(仅名言)",
        "title": "标题(仅案例)",
        "case_type": "案例类型(仅案例)"
    }
    """
    data = request.get_json()
    if not data:
        return error_response("请求体不能为空")
    
    item_type = data.get('type')  # quote or material
    if item_type not in ['quote', 'material']:
        return error_response("必须指定 type 为 quote 或 material")
    
    try:
        db = current_app.config['edurag']['db']
        collection = db.chroma_db._collection
        
        # 获取现有元数据
        existing = collection.get(ids=[item_id])
        if not existing['metadatas']:
            return error_response("项目不存在", 404)
        
        metadata = existing['metadatas'][0]
        
        # 更新字段
        if item_type == 'quote':
            metadata['content'] = data.get('content', metadata.get('content', ''))
            metadata['author'] = data.get('author', metadata.get('author', ''))
            metadata['source'] = data.get('source', metadata.get('source', ''))
        else:
            metadata['content'] = data.get('content', metadata.get('content', ''))
            metadata['title'] = data.get('title', metadata.get('title', ''))
            metadata['type'] = data.get('case_type', metadata.get('type', ''))
        
        # ChromaDB不支持直接update,需要先delete再add
        collection.delete(ids=[item_id])
        collection.add(
            ids=[item_id],
            documents=[metadata.get('content', '')],
            metadatas=[metadata]
        )
        
        logger.info(f"更新{item_type}成功: {item_id}")
        return success_response({'message': '更新成功'})
    
    except Exception as e:
        logger.error(f"更新失败: {e}")
        return error_response(f"服务端错误: {e}", 500)


# ─────────────────────────────────────────────────────────
# DELETE /writing/quotes-materials/<id>  删除名言或案例
# ─────────────────────────────────────────────────────────
@writing_bp.route('/quotes-materials/<item_id>', methods=['DELETE'])
def delete_quote_or_material(item_id):
    """
    删除名言或案例
    """
    try:
        db = current_app.config['edurag']['db']
        collection = db.chroma_db._collection
        
        # 检查是否存在
        existing = collection.get(ids=[item_id])
        if not existing['metadatas']:
            return error_response("项目不存在", 404)
        
        # 删除
        collection.delete(ids=[item_id])
        
        logger.info(f"删除成功: {item_id}")
        return success_response({'message': '删除成功'})
    
    except Exception as e:
        logger.error(f"删除失败: {e}")
        return error_response(f"服务端错误: {e}", 500)


# ─────────────────────────────────────────────────────────
# POST /writing/ai-search-quotes-materials  AI搜索并保存
# ─────────────────────────────────────────────────────────
@writing_bp.route('/ai-search-quotes-materials', methods=['POST'])
def ai_search_and_save():
    """
    使用AI搜索相关名句和素材,并保存到知识库
    
    请求体：
    {
        "topic": "主题关键词（必填）",
        "search_types": ["quotes", "materials"]  # 搜索类型
    }
    
    响应体：
    {
        "success": true,
        "saved_count": 保存数量,
        "quotes_saved": 名言数量,
        "materials_saved": 案例数量
    }
    """
    data = request.get_json()
    if not data:
        return error_response("请求体不能为空")
    
    topic = data.get('topic')
    if not topic:
        return error_response("必须提供 topic 字段")
    
    search_types = data.get('search_types', ['quotes', 'materials'])
    
    try:
        from flask import current_app
        app_config = current_app.config.get('edurag', {})
        llm = app_config.get('llm')
        retriever = app_config.get('retriever')
        db = app_config.get('db')
        
        if not llm or not retriever or not db:
            return error_response("服务端错误: LLM/RAG/DB未初始化", 500)
        
        quotes_saved = 0
        materials_saved = 0
        
        # 1. AI生成名言
        if 'quotes' in search_types:
            system_prompt = f"""你是一位知识渊博的学者，请根据主题“{topic}”提供5-8条相关的名人名言。
要求：
1. 必须是真实存在的名言，不要编造
2. 包含作者和出处信息
3. 格式：每行一条，格式为“名言内容 | 作者 | 出处”
4. 名言要有启发性和教育意义

请直接输出名言列表，不要其他解释："""
            
            result = llm.generate(
                prompt=f"请提供关于“{topic}”的名人名言：",
                system_prompt=system_prompt,
                temperature=0.7
            )
            
            response_text = result.get('response', '')
            lines = response_text.strip().split('\n')
            
            for line in lines:
                if '|' in line:
                    parts = [p.strip() for p in line.split('|')]
                    if len(parts) >= 3:
                        content, author, source = parts[0], parts[1], parts[2]
                        
                        # 保存到ChromaDB
                        import uuid
                        item_id = f"quote_{uuid.uuid4().hex[:12]}"
                        
                        db.chroma_db._collection.add(
                            ids=[item_id],
                            documents=[content],
                            metadatas=[{
                                'type': 'quote',
                                'content': content,
                                'author': author,
                                'source': source,
                                'topic': topic,
                                'created_at': int(time.time() * 1000)
                            }]
                        )
                        quotes_saved += 1
        
        # 2. AI生成案例
        if 'materials' in search_types:
            system_prompt = f"""你是一位历史学家和教育专家，请根据主题“{topic}”提供3-5个相关的真实案例。
要求：
1. 必须是真实的历史事件、人物故事或现实案例，不要编造
2. 每个案例包含标题、详细内容、类型(历史事件/人物故事/现实案例)
3. 格式：每个案例用以下格式
   标题：xxx
   类型：xxx
   内容：xxx
   ---
4. 案例要有教育意义和启发性

请直接输出案例列表，不要其他解释："""
            
            result = llm.generate(
                prompt=f"请提供关于“{topic}”的真实案例：",
                system_prompt=system_prompt,
                temperature=0.7
            )
            
            response_text = result.get('response', '')
            cases = response_text.split('---')
            
            for case in cases:
                case = case.strip()
                if not case:
                    continue
                
                # 解析案例
                title = ''
                case_type = '现实案例'
                content = ''
                
                for line in case.split('\n'):
                    if line.startswith('标题：'):
                        title = line.replace('标题：', '').strip()
                    elif line.startswith('类型：'):
                        case_type = line.replace('类型：', '').strip()
                    elif line.startswith('内容：'):
                        content = line.replace('内容：', '').strip()
                    elif not line.startswith(('标题', '类型', '内容')):
                        content += line + '\n'
                
                if title and content:
                    # 保存到ChromaDB
                    import uuid
                    item_id = f"material_{uuid.uuid4().hex[:12]}"
                    
                    db.chroma_db._collection.add(
                        ids=[item_id],
                        documents=[content],
                        metadatas=[{
                            'type': 'material',
                            'title': title,
                            'content': content,
                            'case_type': case_type,
                            'topic': topic,
                            'created_at': int(time.time() * 1000)
                        }]
                    )
                    materials_saved += 1
        
        logger.info(f"AI搜索完成: 名言{quotes_saved}条, 案例{materials_saved}条")
        
        return success_response({
            'saved_count': quotes_saved + materials_saved,
            'quotes_saved': quotes_saved,
            'materials_saved': materials_saved
        })
    
    except Exception as e:
        logger.error(f"AI搜索失败: {e}")
        return error_response(f"服务端错误: {e}", 500)
