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


def _get_fallback_topics(category: dict) -> list:
    """
    当LLM不可用时，返回预设的示例热点话题
    
    Args:
        category: 分类信息字典
    
    Returns:
        示例热点话题列表
    """
    # 为每个分类准备3个高质量的示例话题
    fallback_data = {
        'technology': [
            {
                'title': '人工智能与人类创造力的边界',
                'category': category['name'],
                'keywords': ['人工智能', '创造力', '人机协作', '科技伦理'],
                'news_summary': '近年来，AI技术在艺术创作、文学写作等领域取得突破性进展。ChatGPT等生成式AI能够创作诗歌、绘画，引发了关于"AI是否具有创造力"的广泛讨论。如何在拥抱技术的同时保持人类的独特价值，成为值得深思的话题。',
                'essay_prompt': '阅读下面的材料，根据要求写作。\n\n材料：2024年，一幅由AI生成的画作在国际艺术大赛中获得金奖，引发了激烈争议。支持者认为AI拓展了创作的边界，反对者则担忧这会削弱人类艺术家的价值。与此同时，作家们也在探讨：当AI能够写出动人的故事时，人类作家的意义何在？\n\n其实，工具从来不是创造的终点，而是起点。关键在于我们如何使用它。\n\n以上材料引发了你怎样的联想和思考？请写一篇文章。\n\n要求：选准角度，确定立意，明确文体，自拟标题；不要套作，不得抄袭；不得泄露个人信息；不少于800字。',
                'writing_angles': [
                    '从"工具理性"与"价值理性"的角度，探讨技术与人文的平衡',
                    '从人类独特性出发，分析情感、直觉在创造中的不可替代性',
                    '从历史维度审视技术革新对传统行业的冲击与机遇',
                ],
                'reference_materials': [
                    '爱因斯坦："想象力比知识更重要"',
                    '达芬奇既是艺术家也是科学家，体现人文与科技的融合',
                    '工业革命时期卢德运动的启示：恐惧源于未知，进步需要理解',
                ],
                'difficulty': '中等',
                'relevance_score': 9,
            },
            {
                'title': '数字时代的"慢生活"追求',
                'category': category['name'],
                'keywords': ['数字化', '快节奏', '慢生活', '心理健康'],
                'news_summary': '在5G、短视频、即时通讯主导的今天，"快"似乎成为时代标签。然而，越来越多的年轻人开始倡导"数字断舍离"，尝试远离手机、回归纸质阅读和面对面交流。这种"慢下来"的生活方式，是对技术的反思，还是对人性本真的回归？',
                'essay_prompt': '阅读下面的材料，根据要求写作。\n\n材料：某中学发起"无手机一周"挑战，起初学生叫苦不迭，但一周后许多人表示感受到了久违的专注和宁静。有人感慨："原来放下手机，世界可以这么清晰。"\n\n在这个万物互联的时代，我们似乎从未如此紧密相连，却又常常感到孤独。"快"与"慢"、"连接"与"独处"，究竟该如何取舍？\n\n请结合材料写一篇文章，体现你的思考。\n\n要求：选准角度，确定立意，明确文体，自拟标题；不要套作，不得抄袭；不少于800字。',
                'writing_angles': [
                    '辩证看待技术发展带来的便利与代价',
                    '从心理学角度分析"注意力经济"对青少年的影响',
                    '探讨真正的"连接"是什么，如何建立有意义的人际关系',
                ],
                'reference_materials': [
                    '梭罗《瓦尔登湖》：简化生活，回归本真',
                    '海德格尔："人诗意地栖居"',
                    '数据显示：现代人平均每天使用手机超过6小时',
                ],
                'difficulty': '容易',
                'relevance_score': 8,
            },
            {
                'title': '算法推荐与信息茧房',
                'category': category['name'],
                'keywords': ['算法', '信息茧房', '多元视角', '独立思考'],
                'news_summary': '短视频平台、新闻资讯APP普遍采用算法推荐机制，为用户推送"感兴趣"的内容。然而，这种个性化服务也可能将人困在"信息茧房"中，只看到自己认同的观点，失去接触多元思想的机会。如何打破茧房，保持开放心态，成为数字公民的重要课题。',
                'essay_prompt': '阅读下面的材料，根据要求写作。\n\n材料：小明发现自己刷短视频时，系统总是推送同类内容，久而久之，他的观点变得越来越极端。直到有一天，他偶然看到一个不同立场的视频，才意识到自己被困在了"信息茧房"里。\n\n算法本身没有善恶，但它塑造的认知环境却可能影响我们的判断。在信息爆炸的时代，保持独立思考显得尤为重要。\n\n以上材料对你有什么启发？请写一篇文章。\n\n要求：选准角度，确定立意，明确文体，自拟标题；不要套作，不得抄袭；不少于800字。',
                'writing_angles': [
                    '从公民素养角度，论述多元信息对社会和谐的重要性',
                    '分析算法背后的商业逻辑及其对个人自由的影响',
                    '提出打破信息茧房的具体方法：主动搜索、跨界阅读等',
                ],
                'reference_materials': [
                    '桑斯坦《信息乌托邦》提出"信息茧房"概念',
                    '柏拉图"洞穴寓言"：走出舒适区才能看到真相',
                    '某平台推出"反推荐"功能，鼓励用户探索多元内容',
                ],
                'difficulty': '较难',
                'relevance_score': 9,
            },
        ],
        'culture': [
            {
                'title': '传统文化的创新表达',
                'category': category['name'],
                'keywords': ['传统文化', '创新', '文化自信', '传承'],
                'news_summary': '从《国家宝藏》到《典籍里的中国》，从故宫文创到汉服复兴，传统文化正以年轻化、时尚化的方式走进大众视野。这种"活化"传承既激发了文化自信，也引发了关于"传统与创新"边界的讨论：如何在创新中保持文化的本真性？',
                'essay_prompt': '阅读下面的材料，根据要求写作。\n\n材料：河南卫视《唐宫夜宴》运用5G+AR技术，让千年文物"活"起来，收获亿万点赞。但也有学者担忧：过度娱乐化是否会消解传统文化的深度？\n\n真正的传承，不是将文化供奉在高阁，而是让它融入当代生活。关键在于把握"度"——既要创新形式，也要守护内核。\n\n请结合材料写一篇文章，谈谈你对传统文化传承的看法。\n\n要求：选准角度，确定立意，明确文体，自拟标题；不要套作，不得抄袭；不少于800字。',
                'writing_angles': [
                    '从"守正创新"的角度，探讨传承与发展的辩证关系',
                    '分析年轻一代为何热衷传统文化，背后的文化认同需求',
                    '对比中外文化传承案例，提炼可借鉴的经验',
                ],
                'reference_materials': [
                    '费孝通："各美其美，美人之美，美美与共，天下大同"',
                    '故宫博物院院长单霁翔：让文物"活"起来的实践',
                    '日本"酷日本"战略：传统文化现代化输出的成功案例',
                ],
                'difficulty': '中等',
                'relevance_score': 9,
            },
        ],
        'environment': [
            {
                'title': '绿色生活方式的选择',
                'category': category['name'],
                'keywords': ['环保', '低碳', '可持续', '个人责任'],
                'news_summary': '碳达峰、碳中和已成为国家战略，但很多人觉得这是政府和企业的责任。事实上，每个人的日常选择——如减少一次性塑料、选择公共交通、节约用电——都在影响着环境。个体行动看似微小，汇聚起来却能产生巨大力量。',
                'essay_prompt': '阅读下面的材料，根据要求写作。\n\n材料：一位高中生坚持自带水杯、拒绝塑料袋一年，减少了约500个塑料瓶的使用。他说："改变世界，先从改变自己开始。"\n\n有人说："一个人的力量太渺小，做不做都一样。"也有人说："每个人都是环境的守护者。"\n\n对此，你怎么看？请写一篇文章。\n\n要求：选准角度，确定立意，明确文体，自拟标题；不要套作，不得抄袭；不少于800字。',
                'writing_angles': [
                    '从"积少成多"的哲理角度，论述个体行动的意义',
                    '分析消费主义对环境的影响，倡导理性消费',
                    '从代际公平角度，探讨我们对后代的责任',
                ],
                'reference_materials': [
                    '蕾切尔·卡森《寂静的春天》：环保意识的觉醒',
                    '"地球一小时"活动：全球数亿人共同参与',
                    '数据显示：如果每人每天节约1度电，全国一年可节约数千亿度',
                ],
                'difficulty': '容易',
                'relevance_score': 8,
            },
        ],
    }
    
    # 返回对应分类的示例数据，如果没有则返回通用示例
    topics = fallback_data.get(category['id'], [])
    if not topics:
        # 通用示例
        topics = [
            {
                'title': f'关注{category["name"]}领域的发展',
                'category': category['name'],
                'keywords': category['keywords'][:3],
                'news_summary': f'当前，{category["name"]}领域正在发生深刻变化，涌现出许多值得关注的现象和趋势。作为新时代的青年，我们应该密切关注这些变化，思考其背后的意义。',
                'essay_prompt': f'阅读下面的材料，根据要求写作。\n\n材料：近年来，{category["name"]}领域发生了诸多变化，既有令人振奋的进步，也有需要警惕的问题。面对这些变化，不同的人有不同的看法。\n\n有人认为应该积极拥抱变化，有人则主张谨慎对待。\n\n请结合你对{category["name"]}领域的了解，写一篇文章，体现你的思考。\n\n要求：选准角度，确定立意，明确文体，自拟标题；不要套作，不得抄袭；不少于800字。',
                'writing_angles': [
                    f'从社会发展的角度分析{category["name"]}领域变化的意义',
                    '探讨个人应该如何应对这些变化',
                    '展望未来发展趋势，提出建设性建议',
                ],
                'reference_materials': [
                    '关注相关新闻报道和政策文件',
                    '查阅专业研究资料',
                    '采访相关领域的专家或从业者',
                ],
                'difficulty': '中等',
                'relevance_score': 7,
            },
        ]
    
    logger.info(f"返回降级数据：{len(topics)} 个示例话题")
    return topics


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
    import time
    
    start_time = time.time()
    data = request.get_json() or {}
    category_id = data.get('category_id')
    use_cache = data.get('use_cache', True)
    force_refresh = data.get('force_refresh', False)
    
    logger.info(f"收到热点搜索请求: category_id={category_id}, use_cache={use_cache}, force_refresh={force_refresh}")
    
    # 确定要搜索的分类
    if category_id:
        categories = [c for c in TOPIC_CATEGORIES if c['id'] == category_id]
        if not categories:
            return jsonify({'error': f'无效的分类ID: {category_id}'}), 400
    else:
        categories = TOPIC_CATEGORIES
    
    logger.info(f"将处理 {len(categories)} 个分类")
    
    all_topics = []
    processed_count = 0
    timeout_count = 0
    max_total_time = 300  # 总超时时间5分钟
    
    for category in categories:
        # 检查总耗时
        elapsed = time.time() - start_time
        if elapsed > max_total_time:
            logger.warning(f"总耗时超过{max_total_time}秒，停止处理剩余分类")
            break
        
        cat_id = category['id']
        processed_count += 1
        
        logger.info(f"[{processed_count}/{len(categories)}] 处理分类: {category['name']}")
        
        # 检查缓存
        cached_topics = None
        if use_cache and not force_refresh:
            cached_topics = _load_cache(cat_id)
            if cached_topics:
                logger.info(f"使用缓存数据，找到 {len(cached_topics)} 个话题")
        
        if cached_topics:
            all_topics.extend(cached_topics)
            continue
        
        # 使用 LLM 生成热点话题
        try:
            logger.info(f"调用LLM生成热点话题...")
            topics = _generate_hot_topics(category)
            if topics:
                _save_cache(cat_id, topics)
                all_topics.extend(topics)
                logger.info(f"成功生成 {len(topics)} 个话题")
            else:
                logger.warning(f"LLM未返回有效数据，使用降级方案")
                fallback_topics = _get_fallback_topics(category)
                all_topics.extend(fallback_topics)
                logger.info(f"使用降级数据，共 {len(fallback_topics)} 个话题")
        except Exception as e:
            timeout_count += 1
            logger.error(f"生成热点话题失败 [{category['name']}]: {e}", exc_info=True)
            # 使用降级数据
            fallback_topics = _get_fallback_topics(category)
            all_topics.extend(fallback_topics)
            logger.info(f"异常后使用降级数据，共 {len(fallback_topics)} 个话题")
            continue
    
    total_elapsed = time.time() - start_time
    logger.info(f"搜索完成，总共返回 {len(all_topics)} 个话题（耗时 {total_elapsed:.1f}秒，超时 {timeout_count} 个分类）")
    
    return jsonify({
        'success': True,
        'topics': all_topics,
        'total': len(all_topics),
        'generated_at': datetime.now().isoformat(),
        'message': f'成功生成 {len(all_topics)} 个热点话题'
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
- 难度适中，适合高中学生

**重要：请严格按照以下JSON格式返回，不要包含任何其他文字：**
[
  {
    "title": "话题标题",
    "category": "分类名称",
    "keywords": ["关键词1", "关键词2", "关键词3"],
    "news_summary": "新闻摘要内容",
    "essay_prompt": "完整的作文题目材料和求",
    "writing_angles": ["角度1", "角度2", "角度3"],
    "reference_materials": ["素材1", "素材2", "素材3"],
    "difficulty": "中等",
    "relevance_score": 8
  }
]"""

    user_query = f"""请分析"{category['name']}"领域的热点话题，并生成高考作文命题预测。

分类信息：
- 分类名称：{category['name']}
- 关键词：{', '.join(category['keywords'])}

请为以下搜索方向生成热点话题分析：
{chr(10).join(f'- {q}' for q in category['search_queries'])}

请直接返回JSON数组，确保：
1. 生成3-5个高质量话题
2. 所有字段都必须存在
3. relevance_score范围是1-10
4. difficulty只能是：容易/中等/较难"""

    # 调用 LLM
    logger.info(f"正在调用LLM生成 [{category['name']}] 的热点话题...")
    logger.debug(f"系统提示词长度: {len(system_prompt)}, 用户查询长度: {len(user_query)}")
    try:
        response = llm.chat(
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_query},
            ],
            temperature=0.7,
            num_predict=3072,  # 增加生成长度
        )
        logger.info(f"LLM响应接收成功，类型: {type(response).__name__}")
        if isinstance(response, dict):
            logger.debug(f"响应字典键: {list(response.keys())}")
        else:
            logger.debug(f"响应长度: {len(str(response))}")
    except Exception as e:
        logger.error(f"LLM调用失败: {e}", exc_info=True)
        raise
    
    # 解析 JSON 响应
    try:
        # 检查response是否为字典（Ollama API返回格式）
        if isinstance(response, dict):
            # Ollama chat API返回格式: {"message": {"role": "...", "content": "..."}, ...}
            if 'message' in response and 'content' in response['message']:
                content = response['message']['content'].strip()
                logger.info(f"从message.content提取内容成功，长度: {len(content)}")
            elif 'choices' in response and len(response['choices']) > 0:
                # OpenAI兼容格式
                content = response['choices'][0].get('text', '').strip()
            elif 'content' in response:
                content = response['content'].strip()
            else:
                logger.error(f"无法从字典响应中提取内容，可用键: {list(response.keys())}")
                logger.error(f"完整响应: {json.dumps(response, ensure_ascii=False)[:500]}")
                return []
        else:
            content = str(response).strip()
        
        logger.debug(f"LLM原始响应前500字符: {content[:500]}")
        
        # 查找 JSON 数组的开始和结束
        start_idx = content.find('[')
        end_idx = content.rfind(']')
        
        if start_idx == -1 or end_idx == -1:
            logger.warning(f"未找到有效的JSON数组格式，响应内容: {content[:200]}...")
            return []
        
        json_str = content[start_idx:end_idx + 1]
        logger.info(f"提取到JSON字符串，长度: {len(json_str)}")
        
        topics = json.loads(json_str)
        logger.info(f"JSON解析成功，共 {len(topics)} 个话题")
        
        # 验证数据结构
        validated_topics = []
        required_fields = ['title', 'essay_prompt']
        
        for i, topic in enumerate(topics):
            if not isinstance(topic, dict):
                logger.warning(f"话题 {i} 不是字典类型，跳过")
                continue
            
            # 检查必需字段
            missing_fields = [f for f in required_fields if f not in topic]
            if missing_fields:
                logger.warning(f"话题 {i} 缺少必需字段: {missing_fields}，跳过")
                continue
            
            # 添加缺失字段的默认值
            topic.setdefault('category', category['name'])
            topic.setdefault('keywords', [])
            topic.setdefault('news_summary', '暂无摘要')
            topic.setdefault('writing_angles', ['从多个角度思考这个话题'])
            topic.setdefault('reference_materials', ['关注相关新闻和时事报道'])
            topic.setdefault('difficulty', '中等')
            
            # 验证相关度评分
            score = topic.get('relevance_score', 5)
            if not isinstance(score, (int, float)) or score < 1 or score > 10:
                topic['relevance_score'] = 5
            
            validated_topics.append(topic)
        
        logger.info(f"验证完成，有效话题数: {len(validated_topics)}")
        return validated_topics
    
    except json.JSONDecodeError as e:
        logger.error(f"JSON解析失败: {e}")
        # 安全地记录响应内容
        try:
            response_str = response if isinstance(response, str) else json.dumps(response, ensure_ascii=False)
            logger.error(f"原始响应片段: {response_str[:1000]}")
        except Exception:
            logger.error(f"无法序列化响应: {type(response)}")
        return []
    except Exception as e:
        logger.error(f"处理响应失败: {e}", exc_info=True)
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
    
    # 正确提取LLM响应内容
    if isinstance(response, dict):
        if 'message' in response and 'content' in response['message']:
            prompt_content = response['message']['content']
        elif 'choices' in response and len(response['choices']) > 0:
            prompt_content = response['choices'][0].get('text', '')
        else:
            return jsonify({'error': '无法解析LLM响应'}), 500
    else:
        prompt_content = str(response)
    
    return jsonify({
        'success': True,
        'prompt': prompt_content,
        'keywords': keywords,
        'essay_type': essay_type,
        'difficulty': difficulty,
    })


# 收藏文件路径
FAVORITES_FILE = os.path.join(
    os.path.dirname(__file__), '..', '..', 'data', 'hot_topics_favorites.json'
)


def _load_favorites() -> list:
    """加载收藏列表"""
    if not os.path.exists(FAVORITES_FILE):
        return []
    try:
        with open(FAVORITES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return []


def _save_favorites(favorites: list):
    """保存收藏列表"""
    os.makedirs(os.path.dirname(FAVORITES_FILE), exist_ok=True)
    with open(FAVORITES_FILE, 'w', encoding='utf-8') as f:
        json.dump(favorites, f, ensure_ascii=False, indent=2)


@hot_topics_bp.route('/favorite', methods=['POST'])
def add_favorite():
    """
    收藏热点话题
    
    Request Body:
        topic: 话题对象（完整的话题数据）
    
    Returns:
        收藏结果
    """
    data = request.get_json() or {}
    topic = data.get('topic')
    
    if not topic:
        return jsonify({'error': '请提供话题数据'}), 400
    
    favorites = _load_favorites()
    
    # 检查是否已收藏（通过标题判断）
    topic_title = topic.get('title', '')
    already_favorited = any(f.get('title') == topic_title for f in favorites)
    
    if already_favorited:
        return jsonify({'success': False, 'message': '该话题已在收藏中'}), 409
    
    # 添加收藏时间
    topic['favorited_at'] = datetime.now().isoformat()
    favorites.append(topic)
    _save_favorites(favorites)
    
    logger.info(f"收藏话题: {topic_title}")
    return jsonify({
        'success': True,
        'message': '收藏成功',
        'total': len(favorites)
    })


@hot_topics_bp.route('/favorite/<topic_title>', methods=['DELETE'])
def remove_favorite(topic_title):
    """
    取消收藏热点话题
    
    Args:
        topic_title: 话题标题（URL编码）
    
    Returns:
        取消收藏结果
    """
    from urllib.parse import unquote
    topic_title = unquote(topic_title)
    
    favorites = _load_favorites()
    original_count = len(favorites)
    favorites = [f for f in favorites if f.get('title') != topic_title]
    
    if len(favorites) == original_count:
        return jsonify({'success': False, 'message': '未找到该话题'}), 404
    
    _save_favorites(favorites)
    logger.info(f"取消收藏话题: {topic_title}")
    return jsonify({
        'success': True,
        'message': '取消收藏成功',
        'total': len(favorites)
    })


@hot_topics_bp.route('/favorites', methods=['GET'])
def get_favorites():
    """
    获取收藏的热点话题列表
    
    Query Params:
        sort_by: 排序方式（created_at/title/relevance_score）
    
    Returns:
        收藏列表
    """
    favorites = _load_favorites()
    sort_by = request.args.get('sort_by', 'favorited_at')
    
    # 排序
    if sort_by == 'title':
        favorites.sort(key=lambda x: x.get('title', ''))
    elif sort_by == 'relevance_score':
        favorites.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
    else:  # favorited_at
        favorites.sort(key=lambda x: x.get('favorited_at', ''), reverse=True)
    
    return jsonify({
        'success': True,
        'topics': favorites,
        'total': len(favorites)
    })
