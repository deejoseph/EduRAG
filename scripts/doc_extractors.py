"""
EduRAG 文档文本提取模块
支持 PDF 和 DOCX 格式的文本提取
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class ExtractedDoc:
    """提取结果"""
    text: str
    page_count: int
    file_path: str
    file_type: str
    extract_success: bool
    error_msg: str = ""


class DocumentExtractor(ABC):
    """文档提取器抽象基类"""

    @abstractmethod
    def extract(self, file_path: str) -> ExtractedDoc:
        """提取文档文本"""
        pass


class PDFExtractor(DocumentExtractor):
    """PDF 文本提取器（使用 pdfplumber）"""

    def extract(self, file_path: str) -> ExtractedDoc:
        try:
            import pdfplumber
        except ImportError:
            return ExtractedDoc(
                text="", page_count=0, file_path=file_path,
                file_type="pdf", extract_success=False,
                error_msg="pdfplumber 未安装，请运行: pip install pdfplumber"
            )

        try:
            pages_text = []
            with pdfplumber.open(file_path) as pdf:
                page_count = len(pdf.pages)
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        pages_text.append(text.strip())

            full_text = "\n\n".join(pages_text)

            if not full_text.strip():
                logger.warning(f"PDF 无文字内容（可能是扫描型）: {file_path}")
                return ExtractedDoc(
                    text="", page_count=page_count, file_path=file_path,
                    file_type="pdf", extract_success=False,
                    error_msg="PDF 无可提取的文字（可能是扫描型 PDF）"
                )

            return ExtractedDoc(
                text=full_text, page_count=page_count, file_path=file_path,
                file_type="pdf", extract_success=True
            )

        except Exception as e:
            logger.error(f"PDF 提取失败 {file_path}: {e}")
            return ExtractedDoc(
                text="", page_count=0, file_path=file_path,
                file_type="pdf", extract_success=False,
                error_msg=str(e)
            )


class DOCXExtractor(DocumentExtractor):
    """DOCX 文本提取器（使用 python-docx）"""

    def extract(self, file_path: str) -> ExtractedDoc:
        try:
            from docx import Document
        except ImportError:
            return ExtractedDoc(
                text="", page_count=0, file_path=file_path,
                file_type="docx", extract_success=False,
                error_msg="python-docx 未安装，请运行: pip install python-docx"
            )

        try:
            doc = Document(file_path)
            paragraphs = []
            for para in doc.paragraphs:
                text = para.text.strip()
                if text:
                    paragraphs.append(text)

            full_text = "\n\n".join(paragraphs)
            # DOCX 没有明确的页数概念，用段落数估算
            page_count = max(1, len(paragraphs) // 30)

            if not full_text.strip():
                logger.warning(f"DOCX 无文字内容: {file_path}")
                return ExtractedDoc(
                    text="", page_count=page_count, file_path=file_path,
                    file_type="docx", extract_success=False,
                    error_msg="DOCX 无可提取的文字"
                )

            return ExtractedDoc(
                text=full_text, page_count=page_count, file_path=file_path,
                file_type="docx", extract_success=True
            )

        except Exception as e:
            logger.error(f"DOCX 提取失败 {file_path}: {e}")
            return ExtractedDoc(
                text="", page_count=0, file_path=file_path,
                file_type="docx", extract_success=False,
                error_msg=str(e)
            )


def get_extractor(file_path: str) -> Optional[DocumentExtractor]:
    """
    根据文件扩展名返回对应的提取器实例

    Args:
        file_path: 文件路径

    Returns:
        DocumentExtractor 实例，不支持的格式返回 None
    """
    ext = Path(file_path).suffix.lower()
    if ext == ".pdf":
        return PDFExtractor()
    elif ext == ".docx":
        return DOCXExtractor()
    else:
        logger.warning(f"不支持的文件格式: {ext} ({file_path})")
        return None
