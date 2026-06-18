"""
知识库检索 API 路由
提供通用的语义检索和集合管理接口
"""

import logging
from flask import Blueprint, request, jsonify, current_app

from api.routes import build_where_filter

logger = logging.getLogger(__name__)

search_bp = Blueprint('search', __name__)


def get_db():
    return current_app.config['edurag']['db']


def get_retriever():
    return current_app.config['edurag']['retriever']


def get_llm():
    return current_app.config['edurag']['llm']


def error_response(message: str, code: int = 400):
    return jsonify({'error': message}), code


def success_response(data: dict):
    return jsonify({'success': True, **data})


# ─────────────────────────────────────────────────────────
# POST /search/query  知识库语义检索
# ─────────────────────────────────────────────────────────
@search_bp.route('/query', methods=['POST'])
def query():
    """
    知识库语义检索接口

    请求体：
    {
        "query": "查询内容（必填）",
        "collection": "集合名称（可选，默认 chinese_essays）",
        "top_k": "返回数量（可选，默认 8）",
        "score_threshold": "相似度阈值（可选，默认 0.25）",
        "with_llm": "是否结合 LLM 生成回答（可选，默认 false）",
        "role": "LLM 角色设定（可选）",
        "expertise": "LLM 专业领域（可选）",
        "filters": {
            "year": 2020,
            "exam_region": "全国卷I",
            "doc_category": "范文",
            "question_type": "作文",
            "grade_level": "高考",
            "subject": "语文",
            "source_type": "exam_paper"
        }
    }

    响应体：
    {
        "success": true,
        "results": [
            {
                "text": "检索内容",
                "score": 0.85,
                "metadata": {...}
            }
        ],
        "count": 8,
        "answer": "LLM 生成的回答（仅 when with_llm=true）"
    }
    """
    data = request.get_json()
    if not data:
        return error_response("请求体不能为空")

    query_text = data.get('query')
    if not query_text:
        return error_response("必须提供 query 字段")

    collection = data.get('collection', 'chinese_essays')
    top_k = data.get('top_k', 8)
    score_threshold = data.get('score_threshold', 0.1)
    with_llm = data.get('with_llm', False)
    role = data.get('role', '教育助手')
    expertise = data.get('expertise', '语文教学与写作指导')
    rerank = data.get('rerank', None)  # None=用全局配置，True/False=覆盖

    # 解析过滤条件
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

    try:
        if with_llm:
            # 使用 RAG pipeline（检索 + LLM 生成）
            rag = current_app.config['edurag']['rag']
            result = rag.query(
                question=query_text,
                collection=collection,
                top_k=top_k,
                score_threshold=score_threshold,
                where=where_filter,
                role=role,
                expertise=expertise,
                rerank=rerank,
            )

            results = [
                {
                    'text': doc,
                    'score': round(score, 4) if score else 0,
                    'metadata': meta,
                }
                for doc, score, meta in zip(
                    result['retrieved_docs'],
                    result.get('scores', []),
                    result['metadatas'],
                )
            ]

            return success_response({
                'results': results,
                'count': len(results),
                'answer': result['answer'],
            })

        else:
            # 纯检索模式（不调用 LLM，速度更快）
            retriever = get_retriever()
            db = get_db()

            # 确保集合存在
            if not db.collection_exists(collection):
                return error_response(f"集合 '{collection}' 不存在")

            result = retriever.search(
                collection_name=collection,
                query=query_text,
                top_k=top_k,
                where=where_filter,
                score_threshold=score_threshold,
                rerank=rerank,
            )

            results = [
                {
                    'text': doc,
                    'score': round(score, 4),
                    'metadata': meta,
                }
                for doc, score, meta in zip(
                    result.documents,
                    result.scores,
                    result.metadatas,
                )
            ]

            return success_response({
                'results': results,
                'count': len(results),
            })

    except Exception as e:
        logger.error(f"检索失败: {e}")
        return error_response(f"服务端错误: {e}", 500)


# ─────────────────────────────────────────────────────────
# GET /search/collections  列出所有集合及文档数
# ─────────────────────────────────────────────────────────
@search_bp.route('/collections', methods=['GET'])
def list_collections():
    """
    列出所有集合及其文档数量

    响应体：
    {
        "success": true,
        "collections": [
            {
                "name": "chinese_essays",
                "count": 27436,
                "metadata": {...}
            }
        ]
    }
    """
    try:
        db = get_db()
        client = db.client
        collection_names = [c.name for c in client.list_collections()]

        collections = []
        for name in collection_names:
            col = client.get_collection(name)
            collections.append({
                'name': name,
                'count': col.count(),
                'metadata': col.metadata,
            })

        return success_response({'collections': collections})

    except Exception as e:
        logger.error(f"列出集合失败: {e}")
        return error_response(f"服务端错误: {e}", 500)


# ─────────────────────────────────────────────────────────
# GET /search/stats  知识库统计信息
# ─────────────────────────────────────────────────────────
@search_bp.route('/stats', methods=['GET'])
def stats():
    """
    知识库统计信息

    响应体：
    {
        "success": true,
        "total_collections": 1,
        "total_documents": 27436,
        "collections": [...],
        "model": "qwen2.5:7b",
        "embedding_model": "BAAI/bge-base-zh-v1.5"
    }
    """
    try:
        db = get_db()
        llm = get_llm()
        config = current_app.config['edurag']['config']

        client = db.client
        collection_names = [c.name for c in client.list_collections()]

        total_docs = 0
        collections = []
        for name in collection_names:
            col = client.get_collection(name)
            count = col.count()
            total_docs += count
            collections.append({
                'name': name,
                'count': count,
            })

        embed_cfg = config.get('embedding', {})

        return success_response({
            'total_collections': len(collections),
            'total_documents': total_docs,
            'collections': collections,
            'llm_model': llm.model,
            'embedding_model': embed_cfg.get('model_name', 'BAAI/bge-base-zh-v1.5'),
        })

    except Exception as e:
        logger.error(f"获取统计信息失败: {e}")
        return error_response(f"服务端错误: {e}", 500)
