"""
作品集 API 路由
学生收藏优秀作文，供温习和积累素材
"""

import os
import uuid
import json
import logging
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify, current_app

logger = logging.getLogger(__name__)

portfolio_bp = Blueprint('portfolio', __name__)

# 数据存储目录
PORTFOLIO_DIR = os.path.join(
    os.path.dirname(__file__), '..', '..', 'data', 'portfolio'
)


def _ensure_dir():
    """确保存储目录存在"""
    os.makedirs(PORTFOLIO_DIR, exist_ok=True)


def _portfolio_path(item_id: str) -> str:
    return os.path.join(PORTFOLIO_DIR, f'{item_id}.json')


def _load_item(item_id: str) -> dict | None:
    path = _portfolio_path(item_id)
    if not os.path.exists(path):
        return None
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def _save_item(item_id: str, data: dict):
    _ensure_dir()
    with open(_portfolio_path(item_id), 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ─────────────────────────────────────────────────────────
# POST /portfolio/add  添加作品到作品集
# ─────────────────────────────────────────────────────────
@portfolio_bp.route('/add', methods=['POST'])
def add_to_portfolio():
    """
    添加作品到作品集

    Request Body:
        content: 作文内容（必需）
        title: 标题（可选，从元数据提取）
        topic: 题目（可选）
        source: 来源（writing/practice/upload）
        metadata: 额外元数据（可选）
        tags: 标签列表（可选）
        ai_feedback: AI 评估结果（可选）
        references: 参考资料（可选）

    Returns:
        新添加的作品 ID 和信息
    """
    data = request.get_json()
    if not data:
        return jsonify({'error': '请求体不能为空'}), 400

    content = data.get('content')
    if not content or not content.strip():
        return jsonify({'error': '作品内容不能为空'}), 400

    item_id = str(uuid.uuid4())
    tags = data.get('tags', [])

    # 验证标签格式
    if not isinstance(tags, list):
        return jsonify({'error': 'tags 必须是数组'}), 400

    item = {
        'id': item_id,
        'title': data.get('title', '未命名作品'),
        'content': content,
        'topic': data.get('topic', ''),
        'source': data.get('source', 'manual'),

        # 高考作文元数据
        'essay_type': data.get('essay_type'),          # 材料作文/话题作文/命题作文/半命题作文
        'essay_style': data.get('essay_style'),        # 议论文/记叙文/说明文/散文
        'grade_level': data.get('grade_level'),        # 高中/初中
        'exam_year': data.get('exam_year'),            # 高考年份
        'exam_region': data.get('exam_region'),        # 考区
        'keywords': data.get('keywords', []),          # 关键词/主题词
        'word_count': len(content.strip()),            # 作文字数

        # 评分信息
        'score': data.get('score'),
        'evaluation_scores': data.get('evaluation_scores'),

        # AI 反馈
        'ai_feedback': data.get('ai_feedback'),
        'references': data.get('references', []),

        # 标签和笔记
        'tags': [tag.strip() for tag in tags if tag.strip()],
        'notes': data.get('notes', ''),

        # 时间戳
        'created_at': _now_iso(),
        'updated_at': _now_iso(),

        # 其他
        'starred': False,
        'metadata': data.get('metadata', {}),
    }

    _save_item(item_id, item)
    logger.info(f"作品已添加到作品集: {item_id}")

    return jsonify({
        'success': True,
        'item_id': item_id,
        'item': item,
    })


# ─────────────────────────────────────────────────────────
# GET /portfolio/list  获取作品集列表（支持筛选和分页）
# ─────────────────────────────────────────────────────────
@portfolio_bp.route('/list', methods=['GET'])
def list_portfolio():
    """
    获取作品集列表

    Query Params:
        page: 页码（默认 1）
        page_size: 每页数量（默认 20）
        tag: 标签过滤
        source: 来源过滤
        keyword: 关键词搜索（标题、内容、题目、关键词）
        starred: 是否只看星标作品（true/false）
        sort_by: 排序字段（created_at/updated_at/score/title/exam_year/word_count）
        sort_order: 排序顺序（asc/desc）
        essay_type: 作文类型过滤
        essay_style: 文体过滤
        grade_level: 学段过滤
        exam_year: 年份过滤
        exam_region: 考区过滤
        min_score: 最低分数
        max_score: 最高分数

    Returns:
        作品列表和分页信息
    """
    _ensure_dir()

    # 查询参数
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('page_size', 20))
    tag_filter = request.args.get('tag', '')
    source_filter = request.args.get('source', '')
    keyword = request.args.get('keyword', '')
    starred = request.args.get('starred', '').lower()
    sort_by = request.args.get('sort_by', 'created_at')
    sort_order = request.args.get('sort_order', 'desc').lower()

    # 新增筛选条件
    essay_type_filter = request.args.get('essay_type', '')
    essay_style_filter = request.args.get('essay_style', '')
    grade_level_filter = request.args.get('grade_level', '')
    exam_year_filter = request.args.get('exam_year', '')
    exam_region_filter = request.args.get('exam_region', '')
    min_score = request.args.get('min_score', '')
    max_score = request.args.get('max_score', '')

    # 加载所有作品
    items = []
    for fname in os.listdir(PORTFOLIO_DIR):
        if not fname.endswith('.json'):
            continue
        fpath = os.path.join(PORTFOLIO_DIR, fname)
        try:
            with open(fpath, 'r', encoding='utf-8') as f:
                item = json.load(f)
            items.append(item)
        except Exception as e:
            logger.error(f"读取作品失败 {fname}: {e}")
            continue

    # 过滤
    if tag_filter:
        items = [i for i in items if tag_filter in i.get('tags', [])]

    if source_filter:
        items = [i for i in items if i.get('source') == source_filter]

    if starred == 'true':
        items = [i for i in items if i.get('starred', False)]
    elif starred == 'false':
        items = [i for i in items if not i.get('starred', False)]

    # 新增筛选条件
    if essay_type_filter:
        items = [i for i in items if i.get('essay_type') == essay_type_filter]

    if essay_style_filter:
        items = [i for i in items if i.get('essay_style') == essay_style_filter]

    if grade_level_filter:
        items = [i for i in items if i.get('grade_level') == grade_level_filter]

    if exam_year_filter:
        try:
            year = int(exam_year_filter)
            items = [i for i in items if i.get('exam_year') == year]
        except ValueError:
            pass

    if exam_region_filter:
        items = [i for i in items if i.get('exam_region') == exam_region_filter]

    if min_score:
        try:
            min_s = float(min_score)
            items = [i for i in items if i.get('score') is not None and i['score'] >= min_s]
        except ValueError:
            pass

    if max_score:
        try:
            max_s = float(max_score)
            items = [i for i in items if i.get('score') is not None and i['score'] <= max_s]
        except ValueError:
            pass

    # 关键词搜索（标题、内容、题目、关键词）
    if keyword:
        keyword_lower = keyword.lower()
        items = [
            i for i in items
            if keyword_lower in i.get('title', '').lower()
            or keyword_lower in i.get('content', '').lower()
            or keyword_lower in i.get('topic', '').lower()
            or any(keyword_lower in kw.lower() for kw in i.get('keywords', []))
        ]

    # 排序
    valid_sort_fields = ['created_at', 'updated_at', 'score', 'title', 'exam_year', 'word_count']
    if sort_by not in valid_sort_fields:
        sort_by = 'created_at'

    # 确定排序方向
    reverse = (sort_order == 'desc')

    # 处理 None 值排序
    def sort_key(item):
        value = item.get(sort_by)
        if value is None:
            return '' if sort_by == 'title' else -1
        return value

    items.sort(key=sort_key, reverse=reverse)

    # 分页
    total = len(items)
    start = (page - 1) * page_size
    end = start + page_size
    page_items = items[start:end]

    # 返回精简版（不包含完整内容）
    summaries = []
    for item in page_items:
        summaries.append({
            'id': item['id'],
            'title': item.get('title', '未命名作品'),
            'topic': item.get('topic', ''),
            'source': item.get('source', ''),

            # 高考作文元数据
            'essay_type': item.get('essay_type'),
            'essay_style': item.get('essay_style'),
            'grade_level': item.get('grade_level'),
            'exam_year': item.get('exam_year'),
            'exam_region': item.get('exam_region'),
            'keywords': item.get('keywords', []),
            'word_count': item.get('word_count'),

            # 评分
            'score': item.get('score'),
            'starred': item.get('starred', False),

            # 时间
            'created_at': item.get('created_at'),
            'updated_at': item.get('updated_at'),

            # 预览
            'content_preview': item.get('content', '')[:200] + ('...' if len(item.get('content', '')) > 200 else ''),
            'has_ai_feedback': item.get('ai_feedback') is not None,
            'has_notes': bool(item.get('notes', '')),
            'tags': item.get('tags', []),
        })

    return jsonify({
        'success': True,
        'items': summaries,
        'total': total,
        'page': page,
        'page_size': page_size,
    })


# ─────────────────────────────────────────────────────────
# GET /portfolio/<item_id>  获取作品详情
# ─────────────────────────────────────────────────────────
@portfolio_bp.route('/<item_id>', methods=['GET'])
def get_item(item_id):
    """获取单个作品的完整信息"""
    item = _load_item(item_id)
    if not item:
        return jsonify({'error': '作品不存在'}), 404

    return jsonify({
        'success': True,
        'item': item,
    })


# ─────────────────────────────────────────────────────────
# PATCH /portfolio/<item_id>  更新作品信息
# ─────────────────────────────────────────────────────────
@portfolio_bp.route('/<item_id>', methods=['PATCH'])
def update_item(item_id):
    """
    更新作品信息

    可更新字段:
        title: 标题
        tags: 标签列表（覆盖）
        notes: 学习笔记
        starred: 是否星标
        metadata: 元数据

    Returns:
        更新后的作品信息
    """
    data = request.get_json()
    if not data:
        return jsonify({'error': '请求体不能为空'}), 400

    item = _load_item(item_id)
    if not item:
        return jsonify({'error': '作品不存在'}), 404

    # 允许更新的字段
    updatable_fields = ['title', 'tags', 'notes', 'starred', 'metadata']

    for field in updatable_fields:
        if field in data:
            if field == 'tags':
                if not isinstance(data[field], list):
                    return jsonify({'error': 'tags 必须是数组'}), 400
                item[field] = [tag.strip() for tag in data[field] if tag.strip()]
            else:
                item[field] = data[field]

    item['updated_at'] = _now_iso()
    _save_item(item_id, item)

    return jsonify({
        'success': True,
        'item': item,
    })


# ─────────────────────────────────────────────────────────
# DELETE /portfolio/<item_id>  删除作品
# ─────────────────────────────────────────────────────────
@portfolio_bp.route('/<item_id>', methods=['DELETE'])
def remove_item(item_id):
    """从作品集中删除作品"""
    path = _portfolio_path(item_id)
    if not os.path.exists(path):
        return jsonify({'error': '作品不存在'}), 404

    os.remove(path)
    logger.info(f"作品已从作品集删除: {item_id}")

    return jsonify({
        'success': True,
        'message': '作品已删除',
    })


# ─────────────────────────────────────────────────────────
# POST /portfolio/<item_id>/toggle-star  切换星标状态
# ─────────────────────────────────────────────────────────
@portfolio_bp.route('/<item_id>/toggle-star', methods=['POST'])
def toggle_star(item_id):
    """切换作品的星标状态"""
    item = _load_item(item_id)
    if not item:
        return jsonify({'error': '作品不存在'}), 404

    item['starred'] = not item.get('starred', False)
    item['updated_at'] = _now_iso()
    _save_item(item_id, item)

    return jsonify({
        'success': True,
        'starred': item['starred'],
    })


# ─────────────────────────────────────────────────────────
# POST /portfolio/<item_id>/add-tag  添加标签
# ─────────────────────────────────────────────────────────
@portfolio_bp.route('/<item_id>/add-tag', methods=['POST'])
def add_tag(item_id):
    """为作品添加标签"""
    data = request.get_json()
    if not data or 'tag' not in data:
        return jsonify({'error': '必须提供 tag 字段'}), 400

    item = _load_item(item_id)
    if not item:
        return jsonify({'error': '作品不存在'}), 404

    tag = data['tag'].strip()
    if not tag:
        return jsonify({'error': '标签不能为空'}), 400

    if tag not in item.get('tags', []):
        item.setdefault('tags', []).append(tag)
        item['updated_at'] = _now_iso()
        _save_item(item_id, item)

    return jsonify({
        'success': True,
        'tags': item['tags'],
    })


# ─────────────────────────────────────────────────────────
# DELETE /portfolio/<item_id>/remove-tag/<tag>  删除标签
# ─────────────────────────────────────────────────────────
@portfolio_bp.route('/<item_id>/remove-tag/<tag>', methods=['DELETE'])
def remove_tag(item_id, tag):
    """删除作品的指定标签"""
    item = _load_item(item_id)
    if not item:
        return jsonify({'error': '作品不存在'}), 404

    if tag in item.get('tags', []):
        item['tags'].remove(tag)
        item['updated_at'] = _now_iso()
        _save_item(item_id, item)

    return jsonify({
        'success': True,
        'tags': item['tags'],
    })


# ─────────────────────────────────────────────────────────
# GET /portfolio/tags  获取所有标签
# ─────────────────────────────────────────────────────────
@portfolio_bp.route('/tags', methods=['GET'])
def get_all_tags():
    """
    获取作品集中所有标签及其使用次数

    Returns:
        标签列表，每个标签包含名称和使用次数
    """
    _ensure_dir()

    tag_counts = {}
    for fname in os.listdir(PORTFOLIO_DIR):
        if not fname.endswith('.json'):
            continue
        fpath = os.path.join(PORTFOLIO_DIR, fname)
        try:
            with open(fpath, 'r', encoding='utf-8') as f:
                item = json.load(f)
            for tag in item.get('tags', []):
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
        except Exception:
            continue

    # 按使用次数降序排列
    tags = [
        {'name': tag, 'count': count}
        for tag, count in sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)
    ]

    return jsonify({
        'success': True,
        'tags': tags,
    })


# ─────────────────────────────────────────────────────────
# POST /portfolio/batch-delete  批量删除
# ─────────────────────────────────────────────────────────
@portfolio_bp.route('/batch-delete', methods=['POST'])
def batch_delete():
    """
    批量删除作品

    Request Body:
        item_ids: 要删除的作品 ID 列表

    Returns:
        删除成功的数量和失败的列表
    """
    data = request.get_json()
    if not data or 'item_ids' not in data:
        return jsonify({'error': '必须提供 item_ids 字段'}), 400

    item_ids = data['item_ids']
    if not isinstance(item_ids, list):
        return jsonify({'error': 'item_ids 必须是数组'}), 400

    deleted = 0
    errors = []

    for item_id in item_ids:
        path = _portfolio_path(item_id)
        if os.path.exists(path):
            try:
                os.remove(path)
                deleted += 1
            except Exception as e:
                errors.append({'item_id': item_id, 'error': str(e)})
        else:
            errors.append({'item_id': item_id, 'error': '作品不存在'})

    return jsonify({
        'success': True,
        'deleted': deleted,
        'errors': errors,
    })


# ─────────────────────────────────────────────────────────
# DELETE /portfolio/reset  重置作品集
# ─────────────────────────────────────────────────────────
@portfolio_bp.route('/reset', methods=['DELETE'])
def reset_portfolio():
    """删除所有作品，重置作品集"""
    _ensure_dir()
    deleted = 0
    errors = []

    for fname in os.listdir(PORTFOLIO_DIR):
        if not fname.endswith('.json'):
            continue
        fpath = os.path.join(PORTFOLIO_DIR, fname)
        try:
            os.remove(fpath)
            deleted += 1
        except Exception as e:
            errors.append(f'{fname}: {e}')

    return jsonify({
        'success': True,
        'deleted': deleted,
        'errors': errors,
    })


# ─────────────────────────────────────────────────────────
# GET /portfolio/stats  获取作品集统计信息
# ─────────────────────────────────────────────────────────
@portfolio_bp.route('/stats', methods=['GET'])
def get_stats():
    """获取作品集的统计信息"""
    _ensure_dir()

    total_items = 0
    tagged_items = 0
    starred_items = 0
    scored_items = 0
    scores = []
    sources = {}
    tag_counts = {}
    essay_types = {}
    essay_styles = {}

    for fname in os.listdir(PORTFOLIO_DIR):
        if not fname.endswith('.json'):
            continue
        fpath = os.path.join(PORTFOLIO_DIR, fname)
        try:
            with open(fpath, 'r', encoding='utf-8') as f:
                item = json.load(f)

            total_items += 1

            if item.get('tags'):
                tagged_items += 1
                for tag in item['tags']:
                    tag_counts[tag] = tag_counts.get(tag, 0) + 1

            if item.get('starred'):
                starred_items += 1

            if item.get('score') is not None:
                scored_items += 1
                scores.append(item['score'])

            source = item.get('source', 'unknown')
            sources[source] = sources.get(source, 0) + 1

            # 统计作文类型
            essay_type = item.get('essay_type')
            if essay_type:
                essay_types[essay_type] = essay_types.get(essay_type, 0) + 1

            # 统计文体
            essay_style = item.get('essay_style')
            if essay_style:
                essay_styles[essay_style] = essay_styles.get(essay_style, 0) + 1

        except Exception:
            continue

    avg_score = round(sum(scores) / len(scores), 1) if scores else 0

    return jsonify({
        'success': True,
        'stats': {
            'total_items': total_items,
            'tagged_items': tagged_items,
            'starred_items': starred_items,
            'scored_items': scored_items,
            'average_score': avg_score,
            'best_score': max(scores) if scores else 0,
            'sources': sources,
            'essay_types': essay_types,
            'essay_styles': essay_styles,
            'top_tags': sorted(
                [{'name': tag, 'count': count} for tag, count in tag_counts.items()],
                key=lambda x: x['count'],
                reverse=True
            )[:10],
        },
    })
