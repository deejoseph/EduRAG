"""
EduRAG 元数据解析模块
从文件名和路径中提取结构化元数据
"""

import re
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger(__name__)

# 年份提取正则（2006-2029）
YEAR_PATTERN = re.compile(r'(20[0-2]\d)\s*年?')

# 考区提取正则
REGION_PATTERN = re.compile(
    r'(全国[ⅠⅡⅢⅣ一二三四I甲乙丙丁]+卷?'
    r'|全国卷[ⅠⅡⅢⅣ一二三四I甲乙丙丁]*'
    r'|全国新高考[ⅠⅡ一二12]卷?'
    r'|高考[甲乙丙丁]卷?'
    r'|北京|上海|天津|浙江|江苏|山东|广东|湖南|湖北|四川|重庆|'
    r'福建|安徽|江西|陕西|辽宁|河北|河南|广西|贵州|云南|'
    r'甘肃|青海|西藏|新疆|海南|黑龙江|吉林|内蒙古|宁夏|山西)'
)

# 标题提取正则（冒号后面的部分）
TITLE_PATTERN = re.compile(r'[：:]\s*(.+?)(?:\.\w+)?$')


def parse_metadata(file_path: str, source_root: str) -> Dict[str, Any]:
    """
    从文件路径和文件名中提取元数据

    Args:
        file_path: 文件的绝对路径
        source_root: 源文件根目录

    Returns:
        元数据字典
    """
    path = Path(file_path)
    root = Path(source_root)

    filename = path.stem  # 不含扩展名的文件名
    file_type = path.suffix.lstrip('.').lower()

    # 相对目录（一级子目录）
    try:
        rel_path = path.relative_to(root)
        source_dir = rel_path.parts[0] if len(rel_path.parts) > 1 else "root"
    except ValueError:
        source_dir = "unknown"

    # 提取年份
    year_match = YEAR_PATTERN.search(filename)
    year = year_match.group(1) if year_match else None
    # 如果文件名中没有年份，尝试从目录名提取
    if year is None:
        year_match = YEAR_PATTERN.search(source_dir)
        year = year_match.group(1) if year_match else None

    # 提取考区
    region_match = REGION_PATTERN.search(filename)
    exam_region = region_match.group(1) if region_match else None

    # 提取标题（冒号后面的部分，或书名号中的内容）
    title = _extract_title(filename)

    # 判定文档类型
    doc_category = _classify_category(filename, source_dir)

    return {
        "source_file": path.name,
        "source_dir": source_dir,
        "file_type": file_type,
        "year": year,
        "exam_region": exam_region,
        "doc_category": doc_category,
        "title": title,
        "imported_at": datetime.now().isoformat(),
    }


def _extract_title(filename: str) -> str:
    """从文件名中提取文章标题"""
    # 尝试提取书名号内容
    book_match = re.search(r'[《「](.+?)[》」]', filename)
    if book_match:
        return book_match.group(1)

    # 尝试提取冒号后的内容
    title_match = TITLE_PATTERN.search(filename)
    if title_match:
        return title_match.group(1).strip()

    # 回退：使用文件名本身（去除常见后缀）
    cleaned = re.sub(r'[-_]\s*备考\d{4}年高考语文作文.*$', '', filename)
    cleaned = re.sub(r'\.\w+$', '', cleaned)
    # 截断过长文件名
    return cleaned[:60] if len(cleaned) > 60 else cleaned


# 学段识别
EXAM_GRADE_PATTERN = re.compile(
    r'(高考|中考|小升初|高一|高二|高三|初一|初二|初三|'
    r'高中|初中|小学|学业水平|会考|模拟|联考|统考)'
)

# 科目识别
SUBJECT_PATTERN = re.compile(
    r'(语文|数学|英语|物理|化学|生物|政治|历史|地理|科学)'
)


def parse_exam_metadata(file_path: str, source_root: str) -> Dict[str, Any]:
    """
    从试卷文件名/路径中提取试卷专用元数据

    适用于真题试卷文件，提取维度比 parse_metadata 更丰富

    Args:
        file_path: 文件绝对路径
        source_root: 源文件根目录

    Returns:
        元数据字典
    """
    path = Path(file_path)
    root = Path(source_root)

    filename = path.stem
    file_type = path.suffix.lstrip('.').lower()

    # 相对目录
    try:
        rel_path = path.relative_to(root)
        source_dir = rel_path.parts[0] if len(rel_path.parts) > 1 else "root"
    except ValueError:
        source_dir = "unknown"

    # 年份
    year_match = YEAR_PATTERN.search(filename) or YEAR_PATTERN.search(source_dir)
    year = year_match.group(1) if year_match else None

    # 考区/卷别
    region_match = REGION_PATTERN.search(filename)
    exam_region = region_match.group(1) if region_match else None

    # 学段
    combined = filename + " " + source_dir
    grade_match = EXAM_GRADE_PATTERN.search(combined)
    grade_level = grade_match.group(1) if grade_match else None

    # 科目
    subject_match = SUBJECT_PATTERN.search(combined)
    subject = subject_match.group(1) if subject_match else None

    return {
        "source_file": path.name,
        "source_dir": source_dir,
        "source_type": "exam_paper",
        "file_type": file_type,
        "year": year,
        "exam_region": exam_region,
        "grade_level": grade_level,
        "subject": subject,
        "doc_category": "真题",
        "title": _extract_title(filename),
        "imported_at": datetime.now().isoformat(),
    }


def _classify_category(filename: str, source_dir: str) -> str:
    """
    根据文件名和目录名判定文档类型

    Returns:
        "范文" / "素材" / "技巧" / "解析" / "综合"
    """
    combined = filename + " " + source_dir

    # 素材类
    if "素材" in source_dir or "素材" in filename:
        return "素材"

    # 解析类
    if "解析" in combined or "评析" in combined or "赏析" in combined:
        return "解析"

    # 技巧类
    technique_keywords = ["技巧", "方法", "审题", "构思", "立意", "写法",
                          "写作指导", "备考方略", "审题十二法"]
    if any(kw in combined for kw in technique_keywords):
        return "技巧"

    # 范文类
    essay_keywords = ["满分作文", "范文", "优秀作文", "精评", "精选",
                      "作文选", "作文集", "佳作"]
    if any(kw in combined for kw in essay_keywords):
        return "范文"

    return "综合"
