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
        
        # 调用LLM生成播客文案
        from core.llm_client import OllamaClient
        llm = OllamaClient(model=model, timeout=180)
        
        system_prompt = """你是一位专业的播客文案策划师，擅长将书面材料转化为生动有趣的播客对话。
你的任务是根据提供的素材，创作出：
1. 开场白自然亲切，吸引听众
2. 内容层次清晰，逻辑连贯
3. 语言口语化，适合听觉接收
4. 适当加入互动和过渡语
5. 结尾有总结或启发

请直接输出播客文案，不需要解释过程。"""
        
        user_prompt = f"""{prompt}

以下是参考素材：

{full_context}

请基于以上素材生成播客文案："""
        
        result = llm.generate(user_prompt, system_prompt=system_prompt, temperature=0.7)
        
        # 更新素材状态为已导入
        for material_id in material_ids:
            manager.update_material_status(material_id, 'imported')
        
        return success_response({
            'script': result.get('response', ''),  # Ollama generate API 返回的是 'response' 字段
            'ai_model': model,
            'materials_count': len(materials)
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
    - ref_audio: 参考音频文件
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
        prompt_text = request.form.get('prompt_text')
        nfe = int(request.form.get('nfe', 18))
        guidance_strength = float(request.form.get('guidance_strength', 3.5))
        
        if not text:
            return error_response("必须提供 text 字段")
        if not prompt_text:
            return error_response("必须提供 prompt_text 字段")
        
        # 获取参考音频文件
        if 'ref_audio' not in request.files:
            return error_response("必须上传 ref_audio 文件")
        
        ref_audio_file = request.files['ref_audio']
        if ref_audio_file.filename == '':
            return error_response("参考音频文件名为空")
        
        # 保存参考音频到临时目录
        import tempfile
        temp_dir = Path(tempfile.mkdtemp())
        ref_audio_path = temp_dir / f"ref_{ref_audio_file.filename}"
        ref_audio_file.save(str(ref_audio_path))
        
        logger.info(f"收到TTS请求: 文本长度={len(text)}, 参考音频={ref_audio_path}")
        
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
        
        # 清理临时文件
        import shutil
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
