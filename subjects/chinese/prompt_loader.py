"""
Prompt 模板加载器
从 subjects/chinese/prompts/ 加载模板文件，解析各段并渲染变量
"""

import os
import logging
from typing import Dict, Optional
from functools import lru_cache

logger = logging.getLogger(__name__)

# 模板目录
PROMPTS_DIR = os.path.join(os.path.dirname(__file__), 'prompts')

# 模板名称到文件的映射
TEMPLATE_MAP = {
    'topic_analysis': 'topic_analysis.txt',
    'outline_gen': 'outline_gen.txt',
    'writing_assist': 'writing_assist.txt',
    'evaluation': 'evaluation.txt',
}


class PromptTemplate:
    """解析后的 Prompt 模板"""

    def __init__(self, name: str, system: str, task: str, output_requirements: str):
        self.name = name
        self.system = system          # [SYSTEM] 段
        self.task = task              # [TASK] 段
        self.output_requirements = output_requirements  # [OUTPUT_REQUIREMENTS] 段

    def render_system(self, **kwargs) -> str:
        """渲染系统提示"""
        try:
            return self.system.format(**kwargs)
        except KeyError as e:
            logger.warning(f"模板 '{self.name}' 系统段缺少变量: {e}")
            return self.system

    def render_task(self, **kwargs) -> str:
        """渲染任务描述"""
        try:
            return self.task.format(**kwargs)
        except KeyError as e:
            logger.warning(f"模板 '{self.name}' 任务段缺少变量: {e}")
            return self.task

    def render_output(self, **kwargs) -> str:
        """渲染输出要求"""
        try:
            return self.output_requirements.format(**kwargs)
        except KeyError as e:
            logger.warning(f"模板 '{self.name}' 输出要求段缺少变量: {e}")
            return self.output_requirements

    def render(self, **kwargs) -> Dict[str, str]:
        """渲染所有段，返回 system_prompt 和 user_query"""
        system_prompt = self.render_system(**kwargs)
        task_text = self.render_task(**kwargs)
        output_text = self.render_output(**kwargs)

        # 合并任务 + 输出要求 作为用户查询
        user_query = f"{task_text}\n\n{output_text}"

        return {
            'system_prompt': system_prompt,
            'user_query': user_query,
        }


def _parse_template(content: str) -> Dict[str, str]:
    """
    解析模板文件，按 [SECTION] 标记分段

    支持的段标记：
    - [SYSTEM]
    - [TASK]
    - [OUTPUT_REQUIREMENTS]

    以 # 开头的行为注释，会被跳过
    """
    sections = {}
    current_section = None
    current_lines = []

    for line in content.split('\n'):
        stripped = line.strip()

        # 跳过注释行
        if stripped.startswith('#'):
            continue

        # 检测段标记
        if stripped.startswith('[') and stripped.endswith(']'):
            # 保存上一段
            if current_section:
                sections[current_section] = '\n'.join(current_lines).strip()

            current_section = stripped[1:-1].upper()
            current_lines = []
        elif current_section:
            current_lines.append(line)

    # 保存最后一段
    if current_section:
        sections[current_section] = '\n'.join(current_lines).strip()

    return sections


@lru_cache(maxsize=16)
def load_template(name: str) -> PromptTemplate:
    """
    加载并解析模板文件（结果缓存）

    Args:
        name: 模板名称（topic_analysis / outline_gen / writing_assist / evaluation）

    Returns:
        PromptTemplate 实例

    Raises:
        FileNotFoundError: 模板文件不存在
        ValueError: 模板缺少必要段
    """
    if name not in TEMPLATE_MAP:
        raise ValueError(f"未知模板: {name}，可选: {list(TEMPLATE_MAP.keys())}")

    filepath = os.path.join(PROMPTS_DIR, TEMPLATE_MAP[name])

    if not os.path.exists(filepath):
        raise FileNotFoundError(f"模板文件不存在: {filepath}")

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    sections = _parse_template(content)

    # 验证必要段
    required = ['SYSTEM', 'TASK', 'OUTPUT_REQUIREMENTS']
    for sec in required:
        if sec not in sections:
            raise ValueError(f"模板 '{name}' 缺少 [{sec}] 段")

    return PromptTemplate(
        name=name,
        system=sections['SYSTEM'],
        task=sections['TASK'],
        output_requirements=sections['OUTPUT_REQUIREMENTS'],
    )


def render_template(name: str, **kwargs) -> Dict[str, str]:
    """
    快捷函数：加载模板并渲染

    Args:
        name: 模板名称
        **kwargs: 模板变量

    Returns:
        {'system_prompt': '...', 'user_query': '...'}
    """
    template = load_template(name)
    return template.render(**kwargs)


# ─────────────────────────────────────────────────────────
# 各场景的便捷渲染函数
# ─────────────────────────────────────────────────────────

def render_topic_analysis(
    topic: str,
    topic_type: str = '',
    grade_level: str = '高中',
) -> Dict[str, str]:
    """渲染审题分析模板"""
    return render_template(
        'topic_analysis',
        topic=topic,
        topic_type=topic_type or '',
        grade_level=grade_level,
    )


def render_outline(
    topic: str,
    thesis: str = '',
    style: str = '议论文',
    word_count: int = 800,
) -> Dict[str, str]:
    """渲染构思提纲模板"""
    # 计算字数分配
    opening_words = int(word_count * 0.15)
    body_words = int(word_count * 0.7)
    ending_words = word_count - opening_words - body_words

    thesis_section = f"立意方向：{thesis}" if thesis else ""

    return render_template(
        'outline_gen',
        topic=topic,
        thesis_section=thesis_section,
        style=style,
        word_count=word_count,
        opening_words=opening_words,
        body_words=body_words,
        ending_words=ending_words,
    )


def render_writing_assist(
    topic: str,
    current_text: str,
    help_type: str = 'polish',
    context: str = '',
) -> Dict[str, str]:
    """渲染写作辅助模板"""
    help_type_desc = {
        'polish': '润色优化',
        'continue': '续写建议',
        'rhetoric': '修辞手法建议',
        'transition': '段落过渡建议',
    }

    context_section = f"补充说明：{context}" if context else ""

    return render_template(
        'writing_assist',
        topic=topic,
        current_text=current_text,
        help_type_desc=help_type_desc.get(help_type, '润色优化'),
        context_section=context_section,
    )


def render_evaluation(
    essay: str,
    topic: str = '',
    grade_level: str = '高中',
    scoring_rubric: list = None,
) -> Dict[str, str]:
    """渲染作文评估模板"""
    if scoring_rubric is None:
        scoring_rubric = ['内容立意', '结构安排', '语言表达', '发展等级']

    rubric_count = len(scoring_rubric)
    dim_score = 100 // rubric_count

    # 构建评分维度模板
    rubric_lines = [f"{i+1}. **{dim}**（{dim_score} 分）" for i, dim in enumerate(scoring_rubric)]
    rubric_template = '\n'.join(rubric_lines)

    topic_section = f"（题目：「{topic}」）" if topic else ""

    return render_template(
        'evaluation',
        topic=topic,
        essay=essay,
        grade_level=grade_level,
        topic_section=topic_section,
        rubric_template=rubric_template,
        dim_score=dim_score,
    )


if __name__ == '__main__':
    # 测试模板加载
    print("模板文件列表:", list(TEMPLATE_MAP.keys()))
    print(f"模板目录: {PROMPTS_DIR}")
    print()

    for name in TEMPLATE_MAP:
        try:
            tpl = load_template(name)
            print(f"[OK] {name}")
            print(f"  SYSTEM: {tpl.system[:50]}...")
            print(f"  TASK: {tpl.task[:50]}...")
            print()
        except Exception as e:
            print(f"[FAIL] {name}: {e}")
