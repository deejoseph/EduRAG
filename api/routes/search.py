"""
知识库检索 API 路由
提供通用的语义检索和集合管理接口
"""

import os
import logging
from pathlib import Path
from urllib.parse import unquote
from flask import Blueprint, request, jsonify, current_app, send_file, abort

from api.routes import build_where_filter

logger = logging.getLogger(__name__)

search_bp = Blueprint('search', __name__)

# 文档存储根目录
DOCS_DIR = Path(__file__).parent.parent.parent / 'data' / 'docs'


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
        logger.error("请求体为空")
        return error_response("请求体不能为空")

    query_text = data.get('query')
    if not query_text:
        logger.error("缺少 query 字段")
        return error_response("必须提供 query 字段")

    collection = data.get('collection', 'chinese_essays')
    top_k = data.get('top_k', 10)
    score_threshold = data.get('score_threshold', 0.01)  # 降低到0.01，支持更多查询
    with_llm = data.get('with_llm', False)
    role = data.get('role', '教育助手')
    expertise = data.get('expertise', '语文教学与写作指导')
    rerank = data.get('rerank', None)  # None=用全局配置，True/False=覆盖
    
    # 记录请求参数
    logger.info(f"🔍 收到检索请求: query='{query_text}', collection={collection}, top_k={top_k}, threshold={score_threshold}, with_llm={with_llm}")

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
    
    if filters:
        logger.info(f"📋 应用过滤条件: {filters}")

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

            logger.info(f"✅ RAG检索完成，返回 {len(results)} 条结果")

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
                logger.error(f"集合 '{collection}' 不存在")
                return error_response(f"集合 '{collection}' 不存在")

            logger.info(f"🔎 执行纯向量检索（无LLM）...")
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

            logger.info(f"✅ 向量检索完成，返回 {len(results)} 条结果")
            if results:
                logger.info(f"   最高相似度: {max(r['score'] for r in results):.4f}")
                logger.info(f"   最低相似度: {min(r['score'] for r in results):.4f}")
            else:
                logger.warning(f"⚠️ 未找到符合条件的结果（阈值={score_threshold}）")

            return success_response({
                'results': results,
                'count': len(results),
            })

    except Exception as e:
        logger.error(f"❌ 检索失败: {e}", exc_info=True)
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


# ─────────────────────────────────────────────────────────
# GET /search/hot-topics  热门关键词/主题统计
# ─────────────────────────────────────────────────────────
@search_bp.route('/hot-topics', methods=['GET'])
def hot_topics():
    """
    获取知识库中的热门关键词和主题统计
    
    响应体：
    {
        "success": true,
        "topics": [
            {
                "name": "责任担当",
                "keywords": ["责任", "担当", "使命", "奉献"],
                "count": 19,
                "max_score": 0.391,
                "description": "高考作文命题重点，关注社会责任与历史使命"
            }
        ],
        "total_topics": 8
    }
    """
    try:
        retriever = get_retriever()
        
        # 定义高考作文常见主题及其关键词
        topic_definitions = {
            '家国情怀': {
                'keywords': ['爱国', '国家', '民族', '祖国'],
                'description': '爱国主义、民族精神、家国责任'
            },
            '责任担当': {
                'keywords': ['责任', '担当', '使命', '奉献'],
                'description': '社会责任、历史使命、奉献精神'
            },
            '文化传承': {
                'keywords': ['文化', '传统', '传承', ' heritage'],
                'description': '传统文化、文化自信、文明传承'
            },
            '科技创新': {
                'keywords': ['科技', '创新', 'AI', '人工智能'],
                'description': '科技发展、创新精神、智能时代'
            },
            '生态文明': {
                'keywords': ['环境', '生态', '绿色', '低碳'],
                'description': '环境保护、绿色发展、可持续发展'
            },
            '青年成长': {
                'keywords': ['青年', '成长', '奋斗', '梦想'],
                'description': '青年责任、成长历程、奋斗精神'
            },
            '人生价值': {
                'keywords': ['价值', '选择', '意义', '理想'],
                'description': '人生价值、价值选择、理想信念'
            },
            '时代精神': {
                'keywords': ['时代', '发展', '变革', '进步'],
                'description': '时代特征、社会进步、改革发展'
            }
        }
        
        # 统计每个主题的相关文档数
        topics_stats = []
        for topic_name, definition in topic_definitions.items():
            total_count = 0
            max_score = 0.0
            
            # 对每个关键词进行搜索
            for keyword in definition['keywords']:
                result = retriever.search(
                    collection_name='chinese_essays',
                    query=keyword,
                    top_k=5,
                    score_threshold=0.05,
                )
                
                # 统计高于阈值的结果
                relevant_docs = [s for s in result.scores if s > 0.05]
                total_count += len(relevant_docs)
                
                if result.scores:
                    max_score = max(max_score, max(result.scores))
            
            topics_stats.append({
                'name': topic_name,
                'keywords': definition['keywords'],
                'count': total_count,
                'max_score': round(max_score, 3),
                'description': definition['description'],
            })
        
        # 按相关文档数排序
        topics_stats.sort(key=lambda x: x['count'], reverse=True)
        
        logger.info(f"✅ 热门主题统计完成，共 {len(topics_stats)} 个主题")
        
        return success_response({
            'topics': topics_stats,
            'total_topics': len(topics_stats),
        })
    
    except Exception as e:
        logger.error(f"获取热门主题失败: {e}", exc_info=True)
        return error_response(f"服务端错误: {e}", 500)


# ─────────────────────────────────────────────────────────
# GET /search/files/<path:filename>  文档文件访问接口
# ─────────────────────────────────────────────────────────
@search_bp.route('/files/<path:subdir>/<filename>', methods=['GET'])
def serve_file(subdir, filename):
    """
    提供文档文件访问服务（智能多目录查找）
    
    支持的文件类型：PDF, DOCX, TXT, MD
    
    URL 示例：
    - /search/files/pdfs/高考满分作文精选39篇.pdf
    - /search/files/docs/专题08 上海卷  2020年高考语文作文解析与范文展示.docx
    
    搜索顺序：
    1. data/docs/<subdir>/<filename> （主要目录）
    2. data/docs/pdfs/ （PDF 默认目录）
    3. data/docs/docs/ （DOCX 默认目录）
    4. data/upload_tmp/ （上传临时目录）
    5. 外部源目录（如果配置）
    
    安全限制：
    - 只允许访问配置的目录下的文件
    - 防止目录穿越攻击
    """
    try:
        # URL 解码（处理中文文件名）
        decoded_filename = unquote(filename)
        decoded_subdir = unquote(subdir)
        
        # 定义可能的搜索根目录（按优先级）
        search_roots = [
            DOCS_DIR / 'all',  # 扁平化目录（所有PDF和DOCX文件）- 最高优先级
            DOCS_DIR / decoded_subdir,  # 请求的子目录
            DOCS_DIR / 'pdfs',  # PDF 默认目录
            DOCS_DIR / 'docs',  # DOCX 默认目录（嵌套子目录）
            DOCS_DIR / 'docs_flat',  # DOCX 扁平目录（所有文件在一层）
            DOCS_DIR / 'texts',  # TXT 默认目录
            DOCS_DIR / 'markdowns',  # MD 默认目录
            Path(__file__).parent.parent.parent / 'data' / 'upload_tmp',  # 上传目录
        ]
        
        # 在所有搜索根目录中查找文件（使用 rglob 全局搜索）
        file_path = None
        logger.info(f"开始搜索文件: {decoded_filename}")
        
        for root_dir in search_roots:
            if not root_dir.exists():
                continue
            
            # 使用 rglob 递归搜索
            matches = list(root_dir.rglob(decoded_filename))
            if matches:
                file_path = matches[0]  # 取第一个匹配
                logger.info(f"找到文件: {file_path}")
                break
        
        if not file_path:
            logger.warning(f"文件不存在于任何搜索路径: {decoded_filename}")
            return error_response(f"文件不存在: {decoded_filename}", 404)
        
        # 安全检查：确保路径在允许的目录内
        allowed_dirs = [
            DOCS_DIR.resolve(),
            (Path(__file__).parent.parent.parent / 'data' / 'upload_tmp').resolve(),
        ]
        try:
            resolved_path = file_path.resolve()
            if not any(resolved_path.is_relative_to(allowed_dir) for allowed_dir in allowed_dirs):
                logger.warning(f"非法文件访问尝试: {resolved_path}")
                return error_response("禁止访问该文件", 403)
        except ValueError:
            logger.warning(f"路径解析失败: {file_path}")
            return error_response("文件路径错误", 400)
        
        # 检查是否为文件（而非目录）
        if not file_path.is_file():
            return error_response("不是有效的文件", 400)
        
        # 根据文件扩展名设置 MIME 类型
        ext = file_path.suffix.lower()
        mime_types = {
            '.pdf': 'application/pdf',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.doc': 'application/msword',
            '.txt': 'text/plain; charset=utf-8',
            '.md': 'text/markdown; charset=utf-8',
        }
        
        mimetype = mime_types.get(ext, 'application/octet-stream')
        
        # 发送文件
        logger.info(f"文件访问: {file_path.relative_to(DOCS_DIR.parent)}")
        return send_file(
            str(file_path),
            mimetype=mimetype,
            as_attachment=False,  # 在线预览而非下载
            download_name=file_path.name
        )
    
    except Exception as e:
        logger.error(f"文件服务错误 ({subdir}/{filename}): {e}")
        return error_response(f"服务端错误: {e}", 500)


# ─────────────────────────────────────────────────────────
# GET /search/files/list  列出所有可用文档
# ─────────────────────────────────────────────────────────
@search_bp.route('/files/list', methods=['GET'])
def list_files():
    """
    列出所有可用的文档文件
    
    查询参数：
    - type: 文件类型过滤 (pdf, docx, txt, md)
    - recursive: 是否递归列出子目录 (true/false, 默认 true)
    
    响应体：
    {
        "success": true,
        "files": [
            {
                "name": "高考满分作文精选39篇.pdf",
                "path": "pdfs/高考满分作文精选39篇.pdf",
                "size": 1776663,
                "type": "pdf"
            }
        ],
        "total": 652
    }
    """
    try:
        # 获取查询参数
        file_type = request.args.get('type', '').lower()
        recursive = request.args.get('recursive', 'true').lower() == 'true'
        
        files = []
        
        if recursive:
            # 优先使用 all/ 目录（扁平化结构）
            all_dir = DOCS_DIR / 'all'
            if all_dir.exists():
                for filename in all_dir.iterdir():
                    if not filename.is_file():
                        continue
                    
                    # 文件类型过滤
                    if file_type and filename.suffix.lower() != f'.{file_type}':
                        continue
                    
                    files.append({
                        'name': filename.name,
                        'path': f'all/{filename.name}',
                        'size': filename.stat().st_size,
                        'type': filename.suffix.lower().lstrip('.'),
                    })
            else:
                # 如果 all/ 目录不存在，则遍历所有子目录
                for root, dirs, filenames in os.walk(DOCS_DIR):
                    for filename in filenames:
                        file_path = Path(root) / filename
                        
                        # 文件类型过滤
                        if file_type and file_path.suffix.lower() != f'.{file_type}':
                            continue
                        
                        # 计算相对路径
                        rel_path = file_path.relative_to(DOCS_DIR)
                        
                        files.append({
                            'name': filename,
                            'path': str(rel_path).replace('\\', '/'),
                            'size': file_path.stat().st_size,
                            'type': file_path.suffix.lower().lstrip('.'),
                        })
        else:
            # 仅列出 all/ 目录（扁平化结构）
            all_dir = DOCS_DIR / 'all'
            if all_dir.exists():
                for item in all_dir.iterdir():
                    if item.is_file():
                        if file_type and item.suffix.lower() != f'.{file_type}':
                            continue
                        
                        files.append({
                            'name': item.name,
                            'path': f'all/{item.name}',
                            'size': item.stat().st_size,
                            'type': item.suffix.lower().lstrip('.'),
                        })
            else:
                # 如果 all/ 目录不存在，则列出根目录
                for item in DOCS_DIR.iterdir():
                    if item.is_file():
                        if file_type and item.suffix.lower() != f'.{file_type}':
                            continue
                        
                        files.append({
                            'name': item.name,
                            'path': item.name,
                            'size': item.stat().st_size,
                            'type': item.suffix.lower().lstrip('.'),
                        })
        
        # 按文件名排序
        files.sort(key=lambda x: x['name'])
        
        return success_response({
            'files': files,
            'total': len(files),
        })
    
    except Exception as e:
        logger.error(f"列出文件失败: {e}")
        return error_response(f"服务端错误: {e}", 500)
