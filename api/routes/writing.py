"""
写作训练 API 路由
提供审题、构思、写作辅助、作文评估四个接口
"""

import logging
from flask import Blueprint, request, jsonify, current_app

from subjects.chinese.prompt_loader import (
    render_topic_analysis,
    render_outline,
    render_writing_assist,
    render_evaluation,
)
from api.routes import build_where_filter

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
