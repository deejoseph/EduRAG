"""
强化训练 API 路由
提供限时自主写作训练：学生先写→AI后反馈→记录进展
"""

import os
import uuid
import json
import logging
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify, current_app

from subjects.chinese.prompt_loader import (
    render_topic_analysis,
    render_outline,
    render_evaluation,
)

logger = logging.getLogger(__name__)

practice_bp = Blueprint('practice', __name__)

# 数据存储目录
PRACTICE_DIR = os.path.join(
    os.path.dirname(__file__), '..', '..', 'data', 'practice_records'
)


def _ensure_dir():
    """确保存储目录存在"""
    os.makedirs(PRACTICE_DIR, exist_ok=True)


def _session_path(session_id: str) -> str:
    return os.path.join(PRACTICE_DIR, f'{session_id}.json')


def _load_session(session_id: str) -> dict | None:
    path = _session_path(session_id)
    if not os.path.exists(path):
        return None
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def _save_session(session_id: str, data: dict):
    _ensure_dir()
    with open(_session_path(session_id), 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _get_rag():
    return current_app.config['edurag']['rag']


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ─────────────────────────────────────────────────────────
# POST /practice/start  创建训练会话
# ─────────────────────────────────────────────────────────
@practice_bp.route('/start', methods=['POST'])
def start():
    """创建限时训练会话，初始化 4 个阶段骨架"""
    data = request.get_json()
    if not data:
        return jsonify({'error': '请求体不能为空'}), 400

    topic = data.get('topic')
    if not topic:
        return jsonify({'error': '必须提供 topic 字段'}), 400

    session_id = str(uuid.uuid4())
    essay_time_limit = data.get('essay_time_limit', 45)  # 分钟
    user_id = data.get('user_id', 'default_user')  # 用户ID，默认 default_user

    session = {
        'id': session_id,
        'user_id': user_id,  # 新增：关联用户ID
        'topic': topic,
        'topic_type': data.get('topic_type', '材料作文'),
        'grade_level': data.get('grade_level', '高中'),
        'started_at': _now_iso(),
        'completed_at': None,
        'total_time_seconds': 0,
        'status': 'in_progress',
        'phases': [
            {
                'type': 'topic_analysis',
                'student_content': '',
                'duration_seconds': 0,
                'suggested_seconds': 600,  # 建议 10 分钟
                'ai_feedback': None,
                'ai_references': [],
                'submitted_at': None,
            },
            {
                'type': 'outline',
                'student_content': '',
                'duration_seconds': 0,
                'suggested_seconds': 900,  # 建议 15 分钟
                'ai_feedback': None,
                'ai_references': [],
                'submitted_at': None,
            },
            {
                'type': 'essay',
                'student_content': '',
                'duration_seconds': 0,
                'suggested_seconds': essay_time_limit * 60,
                'ai_feedback': None,
                'ai_references': [],
                'submitted_at': None,
            },
            {
                'type': 'evaluation',
                'student_content': '',
                'duration_seconds': 0,
                'suggested_seconds': 0,
                'ai_feedback': None,
                'ai_references': [],
                'submitted_at': None,
            },
        ],
        'total_score': None,
        'include_in_log': True,
        'save_to_record': True,
        'evaluation_scores': None,
    }

    _save_session(session_id, session)
    return jsonify({'success': True, 'session_id': session_id, 'session': session})


# ─────────────────────────────────────────────────────────
# POST /practice/save-phase  保存阶段 + AI 反馈
# ─────────────────────────────────────────────────────────
@practice_bp.route('/save-phase', methods=['POST'])
def save_phase():
    """保存学生阶段内容，触发 AI 反馈（评估阶段除外）"""
    data = request.get_json()
    if not data:
        return jsonify({'error': '请求体不能为空'}), 400

    session_id = data.get('session_id')
    phase_type = data.get('phase_type')
    student_content = data.get('student_content', '')
    duration_seconds = data.get('duration_seconds', 0)

    if not session_id or not phase_type:
        return jsonify({'error': '必须提供 session_id 和 phase_type'}), 400

    session = _load_session(session_id)
    if not session:
        return jsonify({'error': '会话不存在'}), 404

    # 找到对应阶段
    phase = None
    for p in session['phases']:
        if p['type'] == phase_type:
            phase = p
            break
    if not phase:
        return jsonify({'error': f'无效的阶段类型: {phase_type}'}), 400

    phase['student_content'] = student_content
    phase['duration_seconds'] = duration_seconds
    phase['submitted_at'] = _now_iso()

    # AI 反馈（essay 阶段不触发 AI，evaluation 阶段触发评估）
    ai_feedback = None
    ai_references = []
    topic = session['topic']
    topic_type = session['topic_type']
    grade_level = session['grade_level']

    try:
        rag = _get_rag()

        if phase_type == 'topic_analysis':
            # 审题对比：把学生分析作为附加上下文
            rendered = render_topic_analysis(
                topic=topic, topic_type=topic_type, grade_level=grade_level,
            )
            user_query = (
                f"{rendered['user_query']}\n\n"
                f"以下是学生自己的审题分析，请对比你的标准分析，指出学生的优点、不足和改进建议：\n\n"
                f"【学生分析】\n{student_content}"
            )
            result = rag.query(
                question=user_query,
                system_prompt=rendered['system_prompt'],
                temperature=0.5,
            )
            ai_feedback = result['answer']
            ai_references = _build_refs(result)

        elif phase_type == 'outline':
            # 提纲对比
            rendered = render_outline(topic=topic, style='议论文', word_count=800)
            user_query = (
                f"{rendered['user_query']}\n\n"
                f"以下是学生自己写的提纲，请对比你的标准提纲，指出学生的优缺点和改进建议：\n\n"
                f"【学生提纲】\n{student_content}"
            )
            result = rag.query(
                question=user_query,
                system_prompt=rendered['system_prompt'],
                temperature=0.6,
            )
            ai_feedback = result['answer']
            ai_references = _build_refs(result)

        elif phase_type == 'essay':
            # 仅保存正文，不触发 AI
            pass

        elif phase_type == 'evaluation':
            # 取阶段 3 的作文内容进行评估
            essay_phase = next(
                (p for p in session['phases'] if p['type'] == 'essay'), None
            )
            essay_text = essay_phase['student_content'] if essay_phase else student_content
            if not essay_text.strip():
                return jsonify({'error': '作文内容为空，无法评估'}), 400

            # 字数门槛检查：高中作文最低 200 字
            char_count = len(essay_text.strip())
            MIN_ESSAY_LENGTH = 200
            if char_count < MIN_ESSAY_LENGTH:
                return jsonify({
                    'error': f'作文内容过短（当前 {char_count} 字），请至少写 {MIN_ESSAY_LENGTH} 字后再提交评估。'
                             f'高考作文要求 800 字以上，目前内容无法进行有效评估。',
                }), 400

            rendered = render_evaluation(
                essay=essay_text, topic=topic, grade_level=grade_level,
            )
            # 评估时增加检索量，提高命中教学讲义的概率
            eval_query = (
                f"{rendered['user_query']} "
                f"作文评分标准 评分维度 立意评估 结构评估 语言评估"
            )
            result = rag.query(
                question=eval_query,
                system_prompt=rendered['system_prompt'],
                temperature=0.4,
            )
            ai_feedback = result['answer']
            ai_references = _build_refs(result)

            # 提取总分和维度分数，并做字数合理性校验
            score = _extract_score(ai_feedback)
            if score is not None:
                # 字数校验：短于 400 字的作文分数上限压制
                if char_count < 400:
                    score = min(score, 40)
                session['total_score'] = score
            dim_scores = _extract_dimension_scores(ai_feedback)
            if dim_scores:
                # 同样对维度分做字数压制
                if char_count < 400:
                    for k in dim_scores:
                        dim_scores[k] = min(dim_scores[k], 10)  # 每维度最高 10/25
                session['evaluation_scores'] = dim_scores

            session['completed_at'] = _now_iso()
            session['status'] = 'completed'

    except Exception as e:
        logger.error(f"AI 反馈生成失败: {e}")
        ai_feedback = f"AI 反馈生成失败: {e}"

    phase['ai_feedback'] = ai_feedback
    phase['ai_references'] = ai_references

    # 计算总用时
    session['total_time_seconds'] = sum(
        p['duration_seconds'] for p in session['phases']
    )

    _save_session(session_id, session)

    return jsonify({
        'success': True,
        'ai_feedback': ai_feedback,
        'references': ai_references,
        'phase': phase,
    })


# ─────────────────────────────────────────────────────────
# GET /practice/history  分页查询历史
# ─────────────────────────────────────────────────────────
@practice_bp.route('/history', methods=['GET'])
def history():
    """分页查询训练历史"""
    _ensure_dir()
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('page_size', 20))

    summaries = []
    for fname in os.listdir(PRACTICE_DIR):
        if not fname.endswith('.json'):
            continue
        fpath = os.path.join(PRACTICE_DIR, fname)
        try:
            with open(fpath, 'r', encoding='utf-8') as f:
                s = json.load(f)
            # 仅显示已保存的记录
            if not s.get('save_to_record', True):
                continue
            summaries.append({
                'id': s['id'],
                'topic': s['topic'],
                'started_at': s['started_at'],
                'total_time_seconds': s.get('total_time_seconds', 0),
                'total_score': s.get('total_score'),
                'status': s.get('status', 'unknown'),
                'phase_count': len([p for p in s.get('phases', []) if p.get('submitted_at')]),
            })
        except Exception:
            continue

    # 按开始时间倒序
    summaries.sort(key=lambda x: x['started_at'], reverse=True)
    total = len(summaries)
    start = (page - 1) * page_size
    end = start + page_size

    return jsonify({
        'success': True,
        'sessions': summaries[start:end],
        'total': total,
        'page': page,
        'page_size': page_size,
    })


# ─────────────────────────────────────────────────────────
# GET /practice/<session_id>  会话详情
# ─────────────────────────────────────────────────────────
@practice_bp.route('/<session_id>', methods=['GET'])
def get_session(session_id):
    session = _load_session(session_id)
    if not session:
        return jsonify({'error': '会话不存在'}), 404
    return jsonify({'success': True, 'session': session})


# ─────────────────────────────────────────────────────────
# DELETE /practice/<session_id>  删除会话
# ─────────────────────────────────────────────────────────
@practice_bp.route('/<session_id>', methods=['DELETE'])
def delete_session(session_id):
    path = _session_path(session_id)
    if not os.path.exists(path):
        return jsonify({'error': '会话不存在'}), 404
    os.remove(path)
    return jsonify({'success': True, 'message': '已删除训练记录'})


# ─────────────────────────────────────────────────────────
# PATCH /practice/<session_id>/toggle-log  切换成长日志计入
# ─────────────────────────────────────────────────────────
@practice_bp.route('/<session_id>/toggle-log', methods=['PATCH'])
def toggle_log(session_id):
    """切换会话是否计入成长日志"""
    data = request.get_json()
    if not data or 'include_in_log' not in data:
        return jsonify({'error': '必须提供 include_in_log 字段'}), 400

    session = _load_session(session_id)
    if not session:
        return jsonify({'error': '会话不存在'}), 404

    session['include_in_log'] = bool(data['include_in_log'])
    _save_session(session_id, session)
    return jsonify({'success': True, 'include_in_log': session['include_in_log']})


# ─────────────────────────────────────────────────────────
# PATCH /practice/<session_id>/save-record  切换保存记录
# ─────────────────────────────────────────────────────────
@practice_bp.route('/<session_id>/save-record', methods=['PATCH'])
def toggle_save_record(session_id):
    """切换会话是否保存到记录（历史和成长日志）"""
    data = request.get_json()
    if not data or 'save_to_record' not in data:
        return jsonify({'error': '必须提供 save_to_record 字段'}), 400

    session = _load_session(session_id)
    if not session:
        return jsonify({'error': '会话不存在'}), 404

    session['save_to_record'] = bool(data['save_to_record'])
    _save_session(session_id, session)
    return jsonify({'success': True, 'save_to_record': session['save_to_record']})


# ─────────────────────────────────────────────────────────
# DELETE /practice/reset-log  重置成长日志
# ─────────────────────────────────────────────────────────
@practice_bp.route('/reset-log', methods=['DELETE'])
def reset_log():
    """删除所有已完成的训练记录，重置成长日志"""
    _ensure_dir()
    deleted = 0
    errors = []

    for fname in os.listdir(PRACTICE_DIR):
        if not fname.endswith('.json'):
            continue
        fpath = os.path.join(PRACTICE_DIR, fname)
        try:
            with open(fpath, 'r', encoding='utf-8') as f:
                s = json.load(f)
            # 仅删除计入成长日志且已完成的记录
            if (s.get('include_in_log', True)
                    and s.get('status') == 'completed'
                    and s.get('save_to_record', True)):
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
# GET /practice/growth-log  成长日志汇总
# ─────────────────────────────────────────────────────────
@practice_bp.route('/growth-log', methods=['GET'])
def growth_log():
    """返回计入成长日志的训练汇总数据"""
    # 获取用户ID参数
    user_id = request.args.get('user_id', 'default_user')
    
    _ensure_dir()
    sessions_data = []

    for fname in os.listdir(PRACTICE_DIR):
        if not fname.endswith('.json'):
            continue
        fpath = os.path.join(PRACTICE_DIR, fname)
        try:
            with open(fpath, 'r', encoding='utf-8') as f:
                s = json.load(f)
            
            # 新增：按用户过滤
            session_user_id = s.get('user_id', 'default_user')
            if session_user_id != user_id:
                continue
            
            if (not s.get('include_in_log', True)
                    or s.get('status') != 'completed'
                    or not s.get('save_to_record', True)):
                continue
            # 提取各阶段用时
            phase_times = {}
            for p in s.get('phases', []):
                phase_times[p['type']] = p.get('duration_seconds', 0)

            sessions_data.append({
                'id': s['id'],
                'user_id': s.get('user_id', 'default_user'),  # 返回用户ID
                'topic': s['topic'],
                'started_at': s['started_at'],
                'total_score': s.get('total_score'),
                'total_time_seconds': s.get('total_time_seconds', 0),
                'phase_times': phase_times,
                'evaluation_scores': s.get('evaluation_scores'),
            })
        except Exception:
            continue

    # 按时间排序
    sessions_data.sort(key=lambda x: x['started_at'])

    # 统计汇总
    scored = [s for s in sessions_data if s['total_score'] is not None]
    summary = {
        'total_sessions': len(sessions_data),
        'average_score': round(sum(s['total_score'] for s in scored) / len(scored), 1) if scored else 0,
        'best_score': max((s['total_score'] for s in scored), default=0),
        'total_training_seconds': sum(s['total_time_seconds'] for s in sessions_data),
    }

    # 分数趋势
    score_trend = [
        {'date': s['started_at'][:10], 'score': s['total_score']}
        for s in scored
    ]

    # 阶段用时趋势
    phase_times = [
        {
            'date': s['started_at'][:10],
            'topic': s['phase_times'].get('topic_analysis', 0),
            'outline': s['phase_times'].get('outline', 0),
            'essay': s['phase_times'].get('essay', 0),
        }
        for s in sessions_data
    ]

    # 维度均分
    dim_keys = ['content', 'structure', 'language', 'development']
    dim_sums = {k: 0 for k in dim_keys}
    dim_count = 0
    for s in sessions_data:
        es = s.get('evaluation_scores')
        if es:
            dim_count += 1
            for k in dim_keys:
                dim_sums[k] += es.get(k, 0)
    dimension_averages = {
        k: round(v / dim_count, 1) if dim_count > 0 else 0
        for k, v in dim_sums.items()
    }

    return jsonify({
        'success': True,
        'sessions': sessions_data,
        'summary': summary,
        'score_trend': score_trend,
        'phase_times': phase_times,
        'dimension_averages': dimension_averages,
    })


# ─── 辅助函数 ──────────────────────────────────────────

def _build_refs(result: dict) -> list:
    """从 RAG 结果构建参考资料列表"""
    return [
        {
            'text': doc[:200] + ('...' if len(doc) > 200 else ''),
            'metadata': meta,
        }
        for doc, meta in zip(
            result.get('retrieved_docs', []),
            result.get('metadatas', []),
        )
    ]


def _extract_score(feedback: str) -> int | None:
    """从评估文本中提取总分数字"""
    import re
    patterns = [
        r'总分[：:]\s*(\d+)',
        r'(\d+)\s*/\s*100',
        r'总分\s*(\d+)\s*分',
    ]
    for pat in patterns:
        m = re.search(pat, feedback)
        if m:
            score = int(m.group(1))
            if 0 <= score <= 100:
                return score
    return None


def _extract_dimension_scores(feedback: str) -> dict | None:
    """从评估文本中提取四个维度的分数"""
    import re
    # 匹配 "**得分**：18/25" 或 "得分：18/25" 或 "得分: 18/25"
    # 按顺序对应: 内容立意、结构安排、语言表达、发展等级
    dim_keys = ['content', 'structure', 'language', 'development']
    pattern = r'\*?\*?得分\*?\*?[：:]\s*(\d+)\s*/\s*(\d+)'
    matches = re.findall(pattern, feedback)

    if not matches:
        return None

    scores = {}
    for i, (score_str, max_str) in enumerate(matches):
        if i < len(dim_keys):
            score = int(score_str)
            max_score = int(max_str)
            # 归一化到 25 分制
            if max_score != 25 and max_score > 0:
                score = round(score * 25 / max_score)
            scores[dim_keys[i]] = min(score, 25)

    return scores if scores else None
