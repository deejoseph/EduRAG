"""
播客文案文本预处理模块
优化断句、多音字、英文缩写等问题，提升TTS质量
"""

import re
from typing import List, Dict


# 常见英文缩写词典（分为三类处理方式）
# 类型1: 按字母逐个读音（推荐）
ABBREVIATIONS_BY_LETTER = {
    "AI", "NASA", "CEO", "CFO", "CTO", "API", "URL", "HTTP", "HTML", "CSS",
    "GDP", "CPI", "NBA", "FIFA", "WHO", "UNESCO", "VIP", "APP", "WiFi",
    "GPS", "USB", "CPU", "GPU", "RAM", "ROM", "PDF", "DOC", "iOS",
}

# 类型2: 翻译为中文含义（适合专业术语）
ABBREVIATIONS_TO_CHINESE = {
    "JavaScript": "杰瓦斯克瑞普特",
    "Python": "派森",
    "Java": "加瓦",
    "Excel": "艾克赛尔",
    "Word": "沃德",
    "PowerPoint": "鲍尔波因特",
    "Photoshop": "佛头秀普",
    "iPhone": "爱疯",
    "iPad": "爱派的",
    "MacBook": "麦克布克",
    "Windows": "温豆斯",
    "Linux": "里纳克斯",
    "Android": "安桌",
}

# 常见多音字词典（格式：词语 -> 拼音标注）
POLYPHONOUS_WORDS = {
    "银行": "yín háng",
    "行走": "xíng zǒu",
    "行业": "háng yè",
    "行动": "xíng dòng",
    "行长": "háng zhǎng",
    "行为": "xíng wéi",
    "重要": "zhòng yào",
    "重复": "chóng fù",
    "重量": "zhòng liàng",
    "重新": "chóng xīn",
    "音乐": "yīn yuè",
    "快乐": "kuài lè",
    "乐曲": "yuè qǔ",
    "欢乐": "huān lè",
    "长大": "zhǎng dà",
    "长短": "cháng duǎn",
    "生长": "shēng zhǎng",
    "长度": "cháng dù",
    "发现": "fā xiàn",
    "头发": "tóu fa",
    "发明": "fā míng",
    "发达": "fā dá",
    "好人": "hǎo rén",
    "爱好": "ài hào",
    "好奇": "hào qí",
    "好处": "hǎo chù",
    "中间": "zhōng jiān",
    "中奖": "zhòng jiǎng",
    "中国": "zhōng guó",
    "看中": "kàn zhòng",
    "分开": "fēn kāi",
    "分量": "fèn liàng",
    "分数": "fēn shù",
    "过分": "guò fèn",
    "要求": "yāo qiú",
    "主要": "zhǔ yào",
    "要领": "yào lǐng",
    "要强": "yào qiáng",
    "没有": "méi yǒu",
    "淹没": "yān mò",
    "没收": "mò shōu",
    "沉没": "chén mò",
    "应该": "yīng gāi",
    "应用": "yìng yòng",
    "响应": "yìng xiǎng",
    "应聘": "yìng pìn",
    "传说": "chuán shuō",
    "传记": "zhuàn jì",
    "传播": "chuán bō",
    "自传": "zì zhuàn",
    "处理": "chǔ lǐ",
    "到处": "dào chù",
    "处分": "chǔ fèn",
    "好处": "hǎo chù",
    "差别": "chā bié",
    "出差": "chū chāi",
    "差距": "chā jù",
    "参差": "cēn cī",
    "曾经": "céng jīng",
    "僧人": "sēng rén",
    "增加": "zēng jiā",
    "赠送": "zèng sòng",
}


class TextPreprocessor:
    """文本预处理器"""
    
    def __init__(self):
        self.abbreviations_by_letter = ABBREVIATIONS_BY_LETTER
        self.abbreviations_to_chinese = ABBREVIATIONS_TO_CHINESE
        self.polyphonic_words = POLYPHONOUS_WORDS
    
    def preprocess(self, text: str) -> str:
        """
        完整的文本预处理流程
        
        Args:
            text: 原始文本
            
        Returns:
            预处理后的文本
        """
        # 1. 基础清洗
        text = self.clean_text(text)
        
        # 2. 数字规范化（包括序号）
        text = self.normalize_numbers(text)
        
        # 3. 数字序号转换（新增）
        text = self.normalize_list_markers(text)
        
        # 4. 英文缩写转换
        text = self.replace_abbreviations(text)
        
        # 5. 特殊符号处理
        text = self.handle_special_symbols(text)
        
        return text
    
    def clean_text(self, text: str) -> str:
        """基础文本清洗"""
        # 去除带括号的场景提示信息（如：（笑声）、（掌声）等）
        text = re.sub(r'[\(（][^\)）]*[\)）]', '', text)
        
        # 去除多余空白
        text = re.sub(r'\s+', ' ', text)
        
        # 去除emoji和特殊字符
        text = re.sub(r'[\U00010000-\U0010ffff]', '', text)
        text = re.sub(r'[\u200b-\u200f\u202a-\u202e]', '', text)
        
        # 统一标点符号
        text = text.replace('"', '"').replace('"', '"')
        text = text.replace("'", "'").replace("'", "'")
        
        return text.strip()
    
    def normalize_numbers(self, text: str) -> str:
        """
        数字规范化
        
        将数字转换为自然语言表述，例如：
        - 2024年 -> 二零二四年
        - 50% -> 百分之五十
        - ¥100 -> 一百元
        """
        # 年份转换
        def replace_year(match):
            year = match.group(1)  # 只捕获数字部分
            digits = ''.join([self._digit_to_chinese(d) for d in year])
            return digits + '年'
        
        text = re.sub(r'(\d{4})年', replace_year, text)  # 用捕获组
        
        # 百分比转换
        def replace_percent(match):
            num = int(match.group(1))
            return f'百分之{self._number_to_chinese(num)}'
        
        text = re.sub(r'(\d+)%', replace_percent, text)
        
        # 金额转换（简化版）
        def replace_money(match):
            amount = float(match.group(1))
            if amount >= 10000:
                return f'{self._number_to_chinese(int(amount/10000))}万元'
            else:
                return f'{self._number_to_chinese(int(amount))}元'
        
        text = re.sub(r'[¥$]([\d.]+)', replace_money, text)
        
        return text
    
    def normalize_list_markers(self, text: str) -> str:
        """
        规范化列表序号和数字标记
        
        处理规则：
        - "1. " → "第一点 "
        - "1、" → "第一点、"
        - "(1)" → "（一）"
        - "第1步" → "第一步"
        - "第2章" → "第二章"
        """
        # 1. 行首的阿拉伯数字序号 → 中文序号
        # "1. 首先" → "第一点 首先"
        def replace_numbered_list(match):
            num = int(match.group(1))
            return f'第{self._number_to_chinese(num)}点'
        
        text = re.sub(r'^\s*(\d+)\.\s*', replace_numbered_list, text, flags=re.MULTILINE)
        
        # "1、首先" → "第一点、首先"
        text = re.sub(r'^\s*(\d+)、\s*', replace_numbered_list, text, flags=re.MULTILINE)
        
        # 2. 带括号的序号
        # "(1)" → "（一）"
        def replace_parenthesized(match):
            num = int(match.group(1))
            return f'（{self._number_to_chinese(num)}）'
        
        text = re.sub(r'\((\d+)\)', replace_parenthesized, text)
        
        # 3. "第X步/章/节/条" 格式
        # "第1步" → "第一步"
        def replace_ordinal(match):
            num = int(match.group(1))
            unit = match.group(2)
            return f'第{self._number_to_chinese(num)}{unit}'
        
        text = re.sub(r'第(\d+)([步章节条])', replace_ordinal, text)
        
        return text
    
    def replace_abbreviations(self, text: str) -> str:
        """
        替换英文缩写为正确读音
        
        处理策略：
        1. 按字母逐个读音（AI → A-I，CEO → C-E-O）
        2. 翻译为中文音译（Python → 派森，Java → 加瓦）
        """
        # 第一步：处理需要翻译为中文的专有名词（优先匹配长的）
        sorted_chinese = sorted(
            self.abbreviations_to_chinese.items(),
            key=lambda x: len(x[0]),
            reverse=True
        )
        
        for abbr, pronunciation in sorted_chinese:
            # 使用更宽松的正则，支持中英文混合
            pattern = re.escape(abbr)
            text = re.sub(pattern, pronunciation, text, flags=re.IGNORECASE)
        
        # 第二步：处理按字母读音的缩写
        # 使用正则找到所有连续的英文大写字母（2个或以上）
        def replace_by_letter(match):
            abbr = match.group(0)
            # 检查是否在按字母读音列表中
            if abbr.upper() in self.abbreviations_by_letter:
                # 将每个字母用空格分开，让TTS逐个读
                return ' '.join(list(abbr.upper()))
            return abbr
        
        # 匹配连续的英文大写字母（2个或以上），前后可以是中文、空格或字符串边界
        pattern = r'(?<![a-zA-Z])([A-Z]{2,})(?![a-zA-Z])'
        text = re.sub(pattern, replace_by_letter, text)
        
        # 特殊处理：混合大小写的缩写（如 iOS、iPhone）
        def replace_mixed_case(match):
            abbr = match.group(0)
            if abbr.upper() in self.abbreviations_by_letter:
                return ' '.join(list(abbr.upper()))
            return abbr
        
        # 匹配以大写字母开头，后面有小写字母，但总长度<=5的短词
        pattern_mixed = r'(?<![a-zA-Z])([A-Z][a-z]{0,4})(?![a-zA-Z])'
        text = re.sub(pattern_mixed, replace_mixed_case, text)
        
        return text
    
    def handle_special_symbols(self, text: str) -> str:
        """处理特殊符号"""
        # 省略号统一
        text = re.sub(r'\.{3,}', '……', text)
        text = text.replace('...', '……')
        
        # 破折号统一
        text = re.sub(r'-{2,}', '——', text)
        
        # 去除多余的空格（保留中英文之间的空格）
        text = re.sub(r'(?<=[\u4e00-\u9fa5])\s+(?=[\u4e00-\u9fa5])', '', text)
        
        return text
    
    def smart_split(self, text: str, max_chars: int = 45, mode: str = 'standard') -> List[str]:
        """
        智能分句，基于语义完整性而非固定字数
        
        Args:
            text: 待分句的文本
            max_chars: 每段最大字符数（会被 mode 覆盖）
            mode: 分段模式
                - 'precise': 精准模式，30字/段（适合重要内容）
                - 'standard': 标准模式，45字/段（默认推荐）
                - 'fast': 快速模式，60字/段（适合草稿）
            
        Returns:
            分句列表
        """
        # 根据模式调整 max_chars
        mode_config = {
            'precise': 30,
            'standard': 45,
            'fast': 60
        }
        
        if mode in mode_config:
            max_chars = mode_config[mode]
        
        # 首先按句子结束符分割
        sentences = re.split(r'(?<=[。！？!?；;])', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            # 如果当前句子加上这句话不超过限制
            if len(current_chunk) + len(sentence) <= max_chars:
                current_chunk += sentence
            else:
                # 如果当前块不为空，先保存
                if current_chunk:
                    chunks.append(current_chunk)
                    current_chunk = ""
                
                # 如果这句话本身就超过限制，需要进一步分割
                if len(sentence) > max_chars:
                    sub_chunks = self._split_long_sentence(sentence, max_chars)
                    chunks.extend(sub_chunks)
                else:
                    current_chunk = sentence
        
        # 添加最后一个块
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks
    
    def _split_long_sentence(self, sentence: str, max_chars: int) -> List[str]:
        """分割长句子，优先在逗号、顿号等处断开"""
        if len(sentence) <= max_chars:
            return [sentence]
        
        # 尝试在逗号处分割
        parts = re.split(r'(?<=[，,、])', sentence)
        parts = [p.strip() for p in parts if p.strip()]
        
        chunks = []
        current = ""
        
        for part in parts:
            if len(current) + len(part) <= max_chars:
                current += part
            else:
                if current:
                    chunks.append(current)
                    current = ""
                
                # 如果这部分本身还是太长，强制分割
                if len(part) > max_chars:
                    for i in range(0, len(part), max_chars):
                        chunks.append(part[i:i+max_chars])
                else:
                    current = part
        
        if current:
            chunks.append(current)
        
        return chunks
    
    def _digit_to_chinese(self, digit: str) -> str:
        """单个数字转中文"""
        mapping = {
            '0': '零', '1': '一', '2': '二', '3': '三', '4': '四',
            '5': '五', '6': '六', '7': '七', '8': '八', '9': '九'
        }
        return mapping.get(digit, digit)
    
    def _number_to_chinese(self, num: int) -> str:
        """数字转中文（简化版，支持0-9999）"""
        if num == 0:
            return '零'
        
        units = ['', '十', '百', '千']
        digits = []
        
        while num > 0:
            digits.append(num % 10)
            num //= 10
        
        result = []
        for i, d in enumerate(reversed(digits)):
            if d != 0:
                result.append(self._digit_to_chinese(str(d)))
                result.append(units[len(digits) - 1 - i])
            elif i < len(digits) - 1 and digits[i + 1] != 0:
                result.append('零')
        
        return ''.join(result).replace('零零', '零').rstrip('零')


# 全局实例
_preprocessor = None


def get_preprocessor() -> TextPreprocessor:
    """获取预处理器实例（单例模式）"""
    global _preprocessor
    if _preprocessor is None:
        _preprocessor = TextPreprocessor()
    return _preprocessor


def preprocess_text(text: str) -> str:
    """便捷函数：预处理文本"""
    return get_preprocessor().preprocess(text)


def smart_split_text(text: str, max_chars: int = 45, mode: str = 'standard') -> List[str]:
    """
    便捷函数：智能分句
    
    Args:
        text: 待分句的文本
        max_chars: 每段最大字符数（会被 mode 覆盖）
        mode: 分段模式 ('precise'/'standard'/'fast')
    
    Returns:
        分句列表
    """
    return get_preprocessor().smart_split(text, max_chars, mode)
