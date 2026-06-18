"""
智能搜索高考命题作文模块
通过搜索新闻、教育动态、时政热点，预测可能成为高考作文的话题
"""

import os
import json
import logging
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, current_app

logger = logging.getLogger(__name__)

hot_topics_bp = Blueprint('hot_topics', __name__)

# 缓存目录
CACHE_DIR = os.path.join(
    os.path.dirname(__file__), '..', '..', 'data', 'hot_topics_cache'
)


def _ensure_cache_dir():
    os.makedirs(CACHE_DIR, exist_ok=True)


def _cache_path(category: str) -> str:
    return os.path.join(CACHE_DIR, f'{category}.json')


def _load_cache(category: str, ttl_hours: int = 24) -> list | None:
    """加载缓存数据，检查是否过期"""
    path = _cache_path(category)
    if not os.path.exists(path):
        return None
    
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        cached_at = datetime.fromisoformat(data.get('cached_at', ''))
        if datetime.now() - cached_at < timedelta(hours=ttl_hours):
            return data.get('topics', [])
        return None
    except Exception:
        return None


def _save_cache(category: str, topics: list):
    """保存缓存数据"""
    _ensure_cache_dir()
    data = {
        'cached_at': datetime.now().isoformat(),
        'topics': topics,
    }
    with open(_cache_path(category), 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _get_llm():
    """获取 LLM 客户端"""
    return current_app.config['edurag']['llm']


def _get_rag():
    """获取 RAG 管道"""
    return current_app.config['edurag']['rag']


# 热点话题分类
TOPIC_CATEGORIES = [
    {
        'id': 'technology',
        'name': '科技发展',
        'keywords': ['人工智能', '科技创新', '数字化', '互联网', '科技伦理', 'AI', 'ChatGPT'],
        'search_queries': [
            '人工智能最新发展 2026',
            '科技创新对社会的影响',
            '数字化时代挑战与机遇',
            '科技伦理问题讨论',
        ],
    },
    {
        'id': 'culture',
        'name': '文化传承',
        'keywords': ['传统文化', '文化自信', '非遗保护', '文化遗产', '国学', '传统美德'],
        'search_queries': [
            '传统文化传承与创新 2026',
            '文化自信建设最新进展',
            '非物质文化遗产保护',
            '中华优秀传统文化弘扬',
        ],
    },
    {
        'id': 'environment',
        'name': '生态文明',
        'keywords': ['环境保护', '绿色发展', '碳中和', '可持续发展', '生态平衡', '低碳生活'],
        'search_queries': [
            '生态文明建设新进展 2026',
            '绿色低碳生活方式',
            '环境保护与经济发展',
            '可持续发展战略实施',
        ],
    },
    {
        'id': 'education',
        'name': '教育改革',
        'keywords': ['素质教育', '教育公平', '终身学习', '教育改革', '人才培养', '创新精神'],
        'search_queries': [
            '教育改革最新政策 2026',
            '素质教育实践案例',
            '教育公平推进措施',
            '创新人才培养模式',
        ],
    },
    {
        'id': 'society',
        'name': '社会责任',
        'keywords': ['青年责任', '社会担当', '志愿服务', '公民素养', '家国情怀', '奋斗精神'],
        'search_queries': [
            '新时代青年责任担当 2026',
            '志愿服务精神弘扬',
            '公民素养提升工程',
            '家国情怀教育实践',
        ],
    },
    {
        'id': 'global',
        'name': '国际视野',
        'keywords': ['全球化', '人类命运共同体', '国际合作', '文化交流', '和平发展', '开放包容'],
        'search_queries': [
            '人类命运共同体理念实践 2026',
            '国际合作与交流新进展',
            '全球化背景下的文化交流',
            '和平发展道路探索',
        ],
    },
]


@hot_topics_bp.route('/categories', methods=['GET'])
def get_categories():
    """获取热点话题分类列表"""
    return jsonify({
        'success': True,
        'categories': TOPIC_CATEGORIES,
    })


@hot_topics_bp.route('/search', methods=['POST'])
def search_hot_topics():
    """
    搜索热点话题并生成高考作文命题预测
    
    Request Body:
        category_id: 分类ID（可选，不传则搜索所有分类）
        use_cache: 是否使用缓存（默认 true）
        force_refresh: 强制刷新（默认 false）
    
    Returns:
        热点话题列表，每个话题包含：
        - title: 话题标题
        - category: 所属分类
        - keywords: 关键词
        - news_summary: 相关新闻摘要
        - essay_prompt: 模拟作文题目
        - writing_angles: 写作角度建议
        - reference_materials: 参考素材
        - difficulty: 难度等级
        - relevance_score: 相关度评分
    """
    data = request.get_json() or {}
    category_id = data.get('category_id')
    use_cache = data.get('use_cache', True)
    force_refresh = data.get('force_refresh', False)
    
    # 确定要搜索的分类
    if category_id:
        categories = [c for c in TOPIC_CATEGORIES if c['id'] == category_id]
        if not categories:
            return jsonify({'error': f'无效的分类ID: {category_id}'}), 400
    else:
        categories = TOPIC_CATEGORIES
    
    all_topics = []
    
    for category in categories:
        cat_id = category['id']
        
        # 检查缓存
        cached_topics = None
        if use_cache and not force_refresh:
            cached_topics = _load_cache(cat_id)
        
        if cached_topics:
            all_topics.extend(cached_topics)
            continue
        
        # 使用 LLM 生成热点话题
        try:
            topics = _generate_hot_topics(category)
            _save_cache(cat_id, topics)
            all_topics.extend(topics)
        except Exception as e:
            logger.error(f"生成热点话题失败 [{category['name']}]: {e}")
            # 返回空列表，继续处理其他分类
            continue
    
    return jsonify({
        'success': True,
        'topics': all_topics,
        'total': len(all_topics),
        'generated_at': datetime.now().isoformat(),
    })


def _generate_hot_topics(category: dict) -> list:
    """
    使用 LLM 生成指定分类的热点话题和命题预测
    
    Args:
        category: 分类信息字典
    
    Returns:
        热点话题列表
    """
    llm = _get_llm()
    
    # 构建提示词
    system_prompt = """你是一位资深的高考语文命题研究专家，擅长分析社会热点并预测高考作文命题趋势。

请根据给定的主题分类和关键词，完成以下任务：
1. 分析当前该领域的社会热点和最新动态
2. 提炼出3-5个可能成为高考作文题目的热点话题
3. 为每个话题设计一个模拟的高考作文题目（材料作文形式）
4. 提供写作角度建议和参考素材

要求：
- 作文题目符合高考命题风格（材料+要求）
- 写作角度要有深度和广度
- 参考素材要具体、有说服力
- 难度适中，适合高中学生"""

    user_query = f"""请分析"{category['name']}"领域的热点话题，并生成高考作文命题预测。

分类信息：
- 分类名称：{category['name']}
- 关键词：{', '.join(category['keywords'])}

请为以下3个搜索方向生成热点话题分析：
{chr(10).join(f'- {q}' for q in category['search_queries'])}

请以JSON数组格式返回，每个话题包含以下字段：
- title: 话题标题（简洁明了）
- category: 分类名称
- keywords: 关键词数组（3-5个）
- news_summary: 相关新闻/现象摘要（100-150字）
- essay_prompt: 模拟作文题目（完整的材料+要求，300-400字）
- writing_angles: 写作角度建议数组（3-4个角度，每个角度一句话）
- reference_materials: 参考素材数组（名人名言、典型案例、数据等，3-4条）
- difficulty: 难度等级（容易/中等/较难）
- relevance_score: 与高考的相关度评分（1-10分）

注意：直接返回JSON数组，不要有其他文字说明。"""

    # 调用 LLM
    response = llm.chat(
        messages=[
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_query},
        ],
        temperature=0.7,
        num_predict=2048,
    )
    
    # 解析 JSON 响应
    try:
        # 尝试提取 JSON 数组
        content = response.strip()
        
        # 查找 JSON 数组的开始和结束
        start_idx = content.find('[')
        end_idx = content.rfind(']')
        
        if start_idx != -1 and end_idx != -1:
            json_str = content[start_idx:end_idx + 1]
            topics = json.loads(json_str)
            
            # 验证数据结构
            validated_topics = []
            for topic in topics:
                if isinstance(topic, dict) and 'title' in topic and 'essay_prompt' in topic:
                    # 添加缺失字段的默认值
                    topic.setdefault('category', category['name'])
                    topic.setdefault('keywords', [])
                    topic.setdefault('news_summary', '')
                    topic.setdefault('writing_angles', [])
                    topic.setdefault('reference_materials', [])
                    topic.setdefault('difficulty', '中等')
                    topic.setdefault('relevance_score', 5)
                    validated_topics.append(topic)
            
            return validated_topics
        else:
            logger.warning(f"未找到有效的JSON数组格式")
            return []
    
    except json.JSONDecodeError as e:
        logger.error(f"JSON解析失败: {e}")
        logger.debug(f"原始响应: {response[:500]}")
        return []
    except Exception as e:
        logger.error(f"处理响应失败: {e}")
        return []


@hot_topics_bp.route('/refresh', methods=['POST'])
def refresh_cache():
    """
    强制刷新缓存
    
    Request Body:
        category_id: 分类ID（可选，不传则刷新所有）
    
    Returns:
        刷新结果
    """
    data = request.get_json() or {}
    category_id = data.get('category_id')
    
    if category_id:
        categories = [c for c in TOPIC_CATEGORIES if c['id'] == category_id]
    else:
        categories = TOPIC_CATEGORIES
    
    refreshed = 0
    errors = []
    
    for category in categories:
        try:
            topics = _generate_hot_topics(category)
            _save_cache(category['id'], topics)
            refreshed += 1
        except Exception as e:
            errors.append(f"{category['name']}: {str(e)}")
    
    return jsonify({
        'success': True,
        'refreshed': refreshed,
        'errors': errors,
    })


@hot_topics_bp.route('/prompt-generator', methods=['POST'])
def generate_custom_prompt():
    """
    自定义命题生成
    
    Request Body:
        keywords: 关键词数组
        essay_type: 作文类型（材料作文/话题作文等）
        difficulty: 难度等级
    
    Returns:
        生成的作文题目
    """
    data = request.get_json() or {}
    keywords = data.get('keywords', [])
    essay_type = data.get('essay_type', '材料作文')
    difficulty = data.get('difficulty', '中等')
    
    if not keywords:
        return jsonify({'error': '请提供至少一个关键词'}), 400
    
    llm = _get_llm()
    
    system_prompt = """你是一位经验丰富的高考语文命题专家。
请根据用户提供的关键词，设计一个符合高考风格的作文题目。

要求：
1. 如果是材料作文，提供一段引人深思的材料（200-300字）
2. 明确写作要求（文体、字数、立意等）
3. 提供立意指导和写作角度建议"""

    user_query = f"""请根据以下关键词生成一个高考作文题目：

关键词：{', '.join(keywords)}
作文类型：{essay_type}
难度等级：{difficulty}

请按以下格式返回：

【作文题目】
（题目内容）

【材料】
（如果是材料作文，提供材料内容）

【要求】
1. 自选角度，确定立意
2. 明确文体（诗歌除外）
3. 不少于800字
4. 不得抄袭、套作

【立意指导】
（2-3个立意角度及简要分析）

【写作角度】
- 角度1：...
- 角度2：...
- 角度3：..."""

    response = llm.chat(
        messages=[
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_query},
        ],
        temperature=0.8,
        num_predict=1024,
    )
    
    return jsonify({
        'success': True,
        'prompt': response,
        'keywords': keywords,
        'essay_type': essay_type,
        'difficulty': difficulty,
    })
