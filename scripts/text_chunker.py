"""
EduRAG 中文文本分块模块
实现适合中文的三级递进分块策略
"""

import logging
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

# 中文分隔符优先级列表（从高到低）
CHINESE_SEPARATORS = ["\n\n", "\n", "。", "！", "？", "；", "，", " "]


@dataclass
class Chunk:
    """文本块"""
    text: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    chunk_index: int = 0
    source_file: str = ""


class ChineseTextChunker:
    """中文文本智能分块器"""

    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        separators: Optional[List[str]] = None,
    ):
        """
        初始化分块器

        Args:
            chunk_size: 每块的目标字数（默认 500，适配 BGE 512 token 上限）
            chunk_overlap: 相邻块重叠字数（默认 50）
            separators: 自定义分隔符列表（按优先级降序）
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators or CHINESE_SEPARATORS

    def chunk_text(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
        source_file: str = "",
    ) -> List[Chunk]:
        """
        将文本分块

        Args:
            text: 原始文本
            metadata: 基础元数据（每个 chunk 继承）
            source_file: 源文件名

        Returns:
            Chunk 列表
        """
        if not text or not text.strip():
            return []

        metadata = metadata or {}

        # 第一级：按自然段落分割
        paragraphs = self._split_by_paragraphs(text)

        # 第二级：超长段落二次切分
        raw_chunks = []
        for para in paragraphs:
            if len(para) <= self.chunk_size:
                raw_chunks.append(para)
            else:
                sub_chunks = self._recursive_split(para)
                raw_chunks.extend(sub_chunks)

        # 第三级：滑动窗口重叠
        chunks_with_overlap = self._apply_overlap(raw_chunks)

        # 构建 Chunk 对象
        results = []
        for i, chunk_text in enumerate(chunks_with_overlap):
            chunk_text = chunk_text.strip()
            if not chunk_text:
                continue

            chunk_meta = {**metadata, "chunk_index": i, "chunk_total": len(chunks_with_overlap)}
            results.append(Chunk(
                text=chunk_text,
                metadata=chunk_meta,
                chunk_index=i,
                source_file=source_file,
            ))

        # 回填真实的 chunk_total（过滤空块后数量可能变化）
        total = len(results)
        for chunk in results:
            chunk.metadata["chunk_total"] = total

        return results

    def chunk_extracted_doc(
        self,
        doc_text: str,
        metadata: Dict[str, Any],
    ) -> List[Chunk]:
        """
        对提取的文档进行分块（便捷方法）

        Args:
            doc_text: 文档文本
            metadata: 元数据（需包含 source_file）

        Returns:
            Chunk 列表
        """
        source_file = metadata.get("source_file", "")
        return self.chunk_text(doc_text, metadata, source_file)

    def _split_by_paragraphs(self, text: str) -> List[str]:
        """按双换行或单换行分割段落，过滤空段落"""
        # 优先按双换行分割
        if "\n\n" in text:
            parts = text.split("\n\n")
        else:
            parts = text.split("\n")

        return [p.strip() for p in parts if p.strip()]

    def _recursive_split(self, text: str, separator_index: int = 0) -> List[str]:
        """
        递归切分超长文本

        Args:
            text: 待切分文本
            separator_index: 当前使用的分隔符索引

        Returns:
            切分后的文本块列表
        """
        if separator_index >= len(self.separators):
            # 所有分隔符都用完了，强制按字数切分
            return self._force_split(text)

        separator = self.separators[separator_index]
        parts = text.split(separator)

        if len(parts) <= 1:
            # 当前分隔符无法切分，尝试下一级
            return self._recursive_split(text, separator_index + 1)

        # 合并小段落到 chunk_size 以内
        merged = []
        current = ""

        for part in parts:
            candidate = current + separator + part if current else part
            if len(candidate) <= self.chunk_size:
                current = candidate
            else:
                if current:
                    merged.append(current.strip())
                # 如果单段仍然超长，递归切分
                if len(part) > self.chunk_size:
                    sub = self._recursive_split(part, separator_index + 1)
                    merged.extend(sub)
                    current = ""
                else:
                    current = part

        if current.strip():
            merged.append(current.strip())

        return merged

    def _force_split(self, text: str) -> List[str]:
        """强制按字数切分（最后的兜底策略）"""
        chunks = []
        start = 0
        while start < len(text):
            end = start + self.chunk_size
            chunks.append(text[start:end].strip())
            start = end
        return [c for c in chunks if c]

    def _apply_overlap(self, chunks: List[str]) -> List[str]:
        """为相邻块添加滑动窗口重叠"""
        if len(chunks) <= 1 or self.chunk_overlap <= 0:
            return chunks

        result = [chunks[0]]

        for i in range(1, len(chunks)):
            prev = chunks[i - 1]
            # 取前一块尾部作为重叠
            overlap_text = prev[-self.chunk_overlap:] if len(prev) > self.chunk_overlap else prev
            current = overlap_text + chunks[i]
            # 确保不超过 chunk_size 太多
            if len(current) > self.chunk_size + self.chunk_overlap:
                current = chunks[i]
            result.append(current)

        return result
