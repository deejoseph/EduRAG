"""
EduRAG 试卷结构化解析模块
将试卷文本分割为独立的题目，识别题型、分值等结构化信息
"""

import re
import logging
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)


# ── 题型分类关键词 ──────────────────────────────────────────
QUESTION_TYPE_KEYWORDS = {
    "作文": ["作文", "写作", "请以", "写一篇", "不少于", "字的文章"],
    "现代文阅读": [
        "现代文阅读", "论述类文本", "实用类文本", "文学类文本",
        "小说阅读", "散文阅读", "信息类文本", "非连续性文本",
        "阅读下面的文字", "阅读下面的材料",
    ],
    "文言文阅读": [
        "文言文阅读", "阅读下面的文言文", "古代诗文阅读",
        "阅读下面这首", "古诗文阅读",
    ],
    "古诗词鉴赏": [
        "古代诗歌阅读", "诗歌鉴赏", "阅读下面这首诗", "阅读下面这首词",
        "诗词鉴赏", "阅读下面的诗歌",
    ],
    "名句默写": [
        "名篇名句默写", "名句名篇默写", "默写", "补写出下列",
        "补写下列名句", "名句填空",
    ],
    "语言运用": [
        "语言文字运用", "语言运用", "语言表达",
        "成语", "病句", "衔接", "压缩", "仿写", "扩写",
        "语段", "在下面一段文字",
    ],
}

# ── 正则模式 ──────────────────────────────────────────
# 大题号：一、 二、 （一） （二） Ⅰ. Ⅱ.
SECTION_PATTERN = re.compile(
    r'^(?:'
    r'[一二三四五六七八九十]+[、．.]\s*'        # 一、 二、
    r'|（[一二三四五六七八九十]+）\s*'          # （一） （二）
    r'|\([一二三四五六七八九十]+\)\s*'          # (一) (二)
    r'|[ⅠⅡⅢⅣⅤ][.．、]\s*'                     # Ⅰ. Ⅱ.
    r')',
    re.MULTILINE
)

# 小题号：1. 2. (1) (2) ① ②
QUESTION_PATTERN = re.compile(
    r'^(?:'
    r'(\d{1,2})[.．、]\s*'                      # 1. 2.
    r'|\((\d{1,2})\)\s*'                         # (1) (2)
    r'|（(\d{1,2})）\s*'                         # （1） （2）
    r'|([①②③④⑤⑥⑦⑧⑨⑩])\s*'                   # ① ②
    r')',
    re.MULTILINE
)

# 分值提取：（6分）(6分) 共6分 满分60分
SCORE_PATTERN = re.compile(
    r'(?:[（(]\s*(\d{1,3})\s*分\s*[）)]'
    r'|共\s*(\d{1,3})\s*分'
    r'|满分\s*(\d{1,3})\s*分'
    r'|本题[共]?(\d{1,3})分)',
)

# 试卷标题中的年份
YEAR_PATTERN = re.compile(r'(20[0-2]\d)\s*年?')

# 试卷标题中的地区/卷别
REGION_PATTERN = re.compile(
    r'('
    r'全国[ⅠⅡⅢⅣ一二三四I甲乙丙丁]+卷?'
    r'|全国卷[ⅠⅡⅢⅣ一二三四I甲乙丙丁]*'
    r'|全国新高考[ⅠⅡ一二12]卷?'
    r'|高考[甲乙丙丁]卷?'
    r'|北京|上海|天津|浙江|江苏|山东|广东|湖南|湖北|'
    r'四川|重庆|福建|安徽|江西|陕西|辽宁|河北|河南|'
    r'广西|贵州|云南|甘肃|青海|西藏|新疆|海南|黑龙江|'
    r'吉林|内蒙古|宁夏|山西'
    r')'
)

# 学段识别
GRADE_LEVEL_PATTERN = re.compile(r'(高考|中考|小升初|高一|高二|高三|初一|初二|初三)')

# 科目识别
SUBJECT_PATTERN = re.compile(r'(语文|数学|英语|物理|化学|生物|政治|历史|地理)')


@dataclass
class ExamQuestion:
    """单道试题"""
    question_number: str              # 题号（如 "1", "一", "(1)"）
    question_text: str                # 题目正文
    question_type: str                # 题型分类
    score: Optional[int] = None       # 分值
    section_name: str = ""            # 所属大题名称
    options: List[str] = field(default_factory=list)  # 选择题选项
    reference_answer: str = ""        # 参考答案（如果有）
    material: str = ""                # 阅读材料（如果有）


@dataclass
class ExamPaper:
    """解析后的试卷"""
    title: str                        # 试卷标题
    year: Optional[str] = None        # 年份
    exam_region: Optional[str] = None # 考区/卷别
    grade_level: Optional[str] = None # 学段（高考/中考）
    subject: Optional[str] = None     # 科目
    total_score: Optional[int] = None # 总分
    questions: List[ExamQuestion] = field(default_factory=list)
    raw_text: str = ""                # 原始文本


class ExamPaperParser:
    """试卷结构化解析器"""

    def parse(self, text: str, source_file: str = "") -> ExamPaper:
        """
        解析试卷全文

        Args:
            text: 试卷全文文本
            source_file: 源文件名

        Returns:
            ExamPaper 结构化结果
        """
        if not text or not text.strip():
            return ExamPaper(title="空文档")

        # 1. 提取试卷级元数据
        title = self._extract_title(text, source_file)
        year = self._extract_year(text, source_file)
        region = self._extract_region(text, source_file)
        grade_level = self._extract_grade_level(text, source_file)
        subject = self._extract_subject(text, source_file)

        # 2. 分割大题（sections）
        sections = self._split_sections(text)

        # 3. 在每个大题内分割小题
        questions = []
        for section_name, section_text in sections:
            section_questions = self._split_questions(section_text)
            section_type = self._classify_section(section_name, section_text)

            for q_num, q_text in section_questions:
                question = self._build_question(
                    q_num, q_text, section_name, section_type
                )
                questions.append(question)

        # 4. 如果没有成功分割出题目，将全文作为一道题
        if not questions:
            logger.debug(f"未能分割题目，将全文作为单题处理: {source_file}")
            q_type = self._classify_section(title, text)
            questions.append(ExamQuestion(
                question_number="1",
                question_text=text.strip()[:2000],
                question_type=q_type or "综合",
                section_name=title,
            ))

        paper = ExamPaper(
            title=title,
            year=year,
            exam_region=region,
            grade_level=grade_level,
            subject=subject or "语文",
            questions=questions,
            raw_text=text,
        )

        logger.info(
            f"解析完成: {title} | {year} {region} | "
            f"{len(questions)} 道题目"
        )
        return paper

    def _extract_title(self, text: str, source_file: str) -> str:
        """提取试卷标题（通常在前3行）"""
        lines = [l.strip() for l in text.split('\n') if l.strip()][:5]

        for line in lines:
            # 匹配常见标题格式
            if any(kw in line for kw in ['试卷', '试题', '考试', '测试', '模拟']):
                return line[:80]

        # 回退到文件名
        if source_file:
            stem = Path(source_file).stem
            return stem[:80]

        return lines[0][:80] if lines else "未知试卷"

    def _extract_year(self, text: str, source_file: str) -> Optional[str]:
        """提取年份"""
        # 先从文件名提取
        if source_file:
            m = YEAR_PATTERN.search(Path(source_file).stem)
            if m:
                return m.group(1)

        # 再从试卷前几行提取
        header = '\n'.join(text.split('\n')[:5])
        m = YEAR_PATTERN.search(header)
        return m.group(1) if m else None

    def _extract_region(self, text: str, source_file: str) -> Optional[str]:
        """提取考区/卷别"""
        # 先从文件名提取
        if source_file:
            m = REGION_PATTERN.search(Path(source_file).stem)
            if m:
                return m.group(1)

        # 再从试卷前几行提取
        header = '\n'.join(text.split('\n')[:5])
        m = REGION_PATTERN.search(header)
        return m.group(1) if m else None

    def _extract_grade_level(self, text: str, source_file: str) -> Optional[str]:
        """提取学段"""
        combined = (Path(source_file).stem if source_file else '') + ' ' + text[:200]
        m = GRADE_LEVEL_PATTERN.search(combined)
        return m.group(1) if m else None

    def _extract_subject(self, text: str, source_file: str) -> Optional[str]:
        """提取科目"""
        combined = (Path(source_file).stem if source_file else '') + ' ' + text[:200]
        m = SUBJECT_PATTERN.search(combined)
        return m.group(1) if m else None

    def _split_sections(self, text: str) -> List[Tuple[str, str]]:
        """
        将试卷分割为大题（sections）

        Returns:
            [(大题名称, 大题文本), ...]
        """
        matches = list(SECTION_PATTERN.finditer(text))

        if len(matches) < 2:
            # 无法分割大题，返回整体
            return [("", text)]

        sections = []
        for i, match in enumerate(matches):
            start = match.start()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)

            section_text = text[start:end].strip()
            # 大题名称 = 匹配行的第一行
            first_line = section_text.split('\n')[0].strip()
            section_name = first_line[:60]

            sections.append((section_name, section_text))

        return sections

    def _split_questions(self, section_text: str) -> List[Tuple[str, str]]:
        """
        在大题文本内分割小题

        Returns:
            [(题号, 题目文本), ...]
        """
        # 先去掉开头的大题标题行，避免被误识别为小题
        cleaned_text = section_text
        section_header_match = SECTION_PATTERN.match(section_text)
        if section_header_match:
            # 去掉大题标题行（可能包含标题后的空行）
            header_end = section_header_match.end()
            # 跳过标题行后面的换行
            while header_end < len(section_text) and section_text[header_end] in '\r\n':
                header_end += 1
            cleaned_text = section_text[header_end:]

        matches = list(QUESTION_PATTERN.finditer(cleaned_text))

        if not matches:
            # 没有小题号：检查剩余文本是否只是阅读材料（非题目）
            # 如果 cleaned_text 太短或只是材料文本，跳过
            stripped = cleaned_text.strip()
            if len(stripped) < 50 or self._is_pure_material(stripped):
                return []
            return [("1", section_text)]

        questions = []
        for i, match in enumerate(matches):
            start = match.start()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(cleaned_text)

            q_text = cleaned_text[start:end].strip()

            # 提取题号
            q_num = match.group(1) or match.group(2) or match.group(3) or match.group(4) or str(i + 1)

            questions.append((q_num, q_text))

        return questions

    def _is_pure_material(self, text: str) -> bool:
        """判定文本是否纯为阅读材料（非题目）"""
        # 常见材料提示语
        material_markers = [
            "阅读下面的文字", "阅读下面的材料", "阅读下面的文言文",
            "阅读下面这首诗", "阅读下面这首词", "阅读下面的诗歌",
            "补写出下列", "名篇名句默写",
        ]
        if any(m in text for m in material_markers):
            # 检查是否有题目要求
            question_markers = ["下列", "请", "不正确", "正确", "概括", "分析", "简要"]
            if not any(q in text for q in question_markers):
                return True
        return False

    def _classify_section(self, section_name: str, section_text: str) -> str:
        """根据大题名称和内容判定题型
        
        两轮匹配策略：
        1. 先用 section_name（大题标题）精确匹配
        2. 未命中时再用 text 前 80 字补充
        """
        # 第一轮：只匹配大题标题
        for q_type, keywords in QUESTION_TYPE_KEYWORDS.items():
            if any(kw in section_name for kw in keywords):
                return q_type

        # 第二轮：用文本前缀补充（避免选项文本干扰）
        text_prefix = section_text[:80] if section_text else ""
        for q_type, keywords in QUESTION_TYPE_KEYWORDS.items():
            if any(kw in text_prefix for kw in keywords):
                return q_type

        return "综合"

    def _build_question(
        self, q_num: str, q_text: str, section_name: str, section_type: str
    ) -> ExamQuestion:
        """构建单道题目对象"""
        # 提取分值
        score = None
        score_matches = SCORE_PATTERN.findall(q_text)
        if score_matches:
            for groups in score_matches:
                for g in groups:
                    if g:
                        score = int(g)
                        break
                if score:
                    break

        # 提取选项
        options = []
        option_pattern = re.compile(r'^([A-D])[.．、]\s*(.+)', re.MULTILINE)
        option_matches = option_pattern.findall(q_text)
        if len(option_matches) >= 2:
            options = [f"{letter}. {content.strip()}" for letter, content in option_matches]

        # 尝试分离阅读材料和题目要求
        material, question_body = self._split_material_and_question(q_text, section_type)

        return ExamQuestion(
            question_number=q_num,
            question_text=question_body if question_body else q_text,
            question_type=section_type,
            score=score,
            section_name=section_name,
            options=options,
            material=material,
        )

    def _split_material_and_question(
        self, text: str, q_type: str
    ) -> Tuple[str, str]:
        """
        分离阅读材料和题目要求

        对于阅读类题目，通常前半段是材料，后半段是题目要求
        """
        if q_type not in ("现代文阅读", "文言文阅读", "古诗词鉴赏"):
            return "", text

        # 常见分隔模式
        separators = [
            r'\n\s*(?:题目|问题|请回答|请简要|阅读后|下列)',
            r'\n\s*[\(（]\s*\d',  # 第N题开始的编号
        ]

        for sep in separators:
            m = re.search(sep, text)
            if m and m.start() > len(text) * 0.3:
                # 分隔点至少在文本30%处，确保前面确实是材料
                return text[:m.start()].strip(), text[m.start():].strip()

        return "", text
