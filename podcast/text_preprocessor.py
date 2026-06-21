"""
播客文案文本预处理模块
优化断句、多音字、英文缩写等问题，提升TTS质量
"""

import re
from typing import List, Dict


# 常见英文缩写词典（格式：缩写 -> 正确读音）
ENGLISH_ABBREVIATIONS = {
    "AI": "人工智能",
    "NASA": "美国航空航天局",
    "CEO": "首席执行官",
    "CFO": "首席财务官",
    "CTO": "首席技术官",
    "API": "应用程序接口",
    "URL": "统一资源定位符",
    "HTTP": "超文本传输协议",
    "HTML": "超文本标记语言",
    "CSS": "层叠样式表",
    "JavaScript": "杰瓦斯克瑞普特",
    "Python": "派森",
    "Java": "加瓦",
    "GDP": "国内生产总值",
    "CPI": "消费者物价指数",
    "NBA": "美国职业篮球联赛",
    "FIFA": "国际足球联合会",
    "WHO": "世界卫生组织",
    "UNESCO": "联合国教科文组织",
    "VIP": "贵宾",
    "APP": "应用程序",
    "WiFi": "无线网络",
    "GPS": "全球定位系统",
    "USB": "通用串行总线",
    "CPU": "中央处理器",
    "GPU": "图形处理器",
    "RAM": "随机存取存储器",
    "ROM": "只读存储器",
    "PDF": "便携式文档格式",
    "DOC": "文档",
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
    "iOS": "爱偶艾斯",
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
        self.abbreviations = ENGLISH_ABBREVIATIONS
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
        
        # 2. 数字规范化
        text = self.normalize_numbers(text)
        
        # 3. 英文缩写转换
        text = self.replace_abbreviations(text)
        
        # 4. 特殊符号处理
        text = self.handle_special_symbols(text)
        
        return text
    
    def clean_text(self, text: str) -> str:
        """基础文本清洗"""
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
            year = match.group(0)
            digits = ''.join([self._digit_to_chinese(d) for d in year])
            return digits + '年'
        
        text = re.sub(r'\d{4}年', replace_year, text)
        
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
    
    def replace_abbreviations(self, text: str) -> str:
        """替换英文缩写为中文读音"""
        # 按长度降序排列，优先匹配长的缩写
        sorted_abbrs = sorted(
            self.abbreviations.items(),
            key=lambda x: len(x[0]),
            reverse=True
        )
        
        for abbr, pronunciation in sorted_abbrs:
            # 使用正则确保完整匹配单词边界
            pattern = r'\b' + re.escape(abbr) + r'\b'
            text = re.sub(pattern, pronunciation, text, flags=re.IGNORECASE)
        
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
    
    def smart_split(self, text: str, max_chars: int = 40) -> List[str]:
        """
        智能分句，基于语义完整性而非固定字数
        
        Args:
            text: 待分句的文本
            max_chars: 每段最大字符数
            
        Returns:
            分句列表
        """
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


def smart_split_text(text: str, max_chars: int = 40) -> List[str]:
    """便捷函数：智能分句"""
    return get_preprocessor().smart_split(text, max_chars)
