"""
EduRAG API 路由模块
"""

from typing import Dict, Optional


def build_where_filter(
    year: Optional[int] = None,
    exam_region: Optional[str] = None,
    doc_category: Optional[str] = None,
    file_type: Optional[str] = None,
    question_type: Optional[str] = None,
    grade_level: Optional[str] = None,
    subject: Optional[str] = None,
    source_type: Optional[str] = None,
) -> Optional[Dict]:
    """
    构建 ChromaDB where 过滤条件

    支持的过滤字段：
    - year: 年份（整数，如 2020）
    - exam_region: 考区（字符串，如 "全国卷I"、"北京"）
    - doc_category: 文档类型（范文/素材/技巧/解析/综合/真题）
    - file_type: 文件类型（pdf/docx）
    - question_type: 题型（作文/现代文阅读/文言文阅读/古诗词鉴赏/名句默写/语言运用/综合）
    - grade_level: 学段（高考/中考/高一/高二/高三 等）
    - subject: 科目（语文/数学/英语 等）
    - source_type: 来源类型（exam_paper / 默认无）

    Returns:
        ChromaDB where 字典，或 None（无过滤条件时）
    """
    conditions = []

    if year is not None:
        conditions.append({"year": {"$eq": str(year)}})
    if exam_region:
        conditions.append({"exam_region": {"$eq": exam_region}})
    if doc_category:
        conditions.append({"doc_category": {"$eq": doc_category}})
    if file_type:
        conditions.append({"file_type": {"$eq": file_type}})
    if question_type:
        conditions.append({"question_type": {"$eq": question_type}})
    if grade_level:
        conditions.append({"grade_level": {"$eq": grade_level}})
    if subject:
        conditions.append({"subject": {"$eq": subject}})
    if source_type:
        conditions.append({"source_type": {"$eq": source_type}})

    if not conditions:
        return None
    elif len(conditions) == 1:
        return conditions[0]
    else:
        return {"$and": conditions}
