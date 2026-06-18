"""
EduRAG 真题库导入脚本
支持将 PDF/DOCX 格式的试卷解析为独立题目，导入向量数据库
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import argparse
import hashlib
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Set, Dict, Any, Optional

from tqdm import tqdm

from core.embedding import EmbeddingModel
from core.db_manager import EduRAGDatabase
from scripts.doc_extractors import get_extractor
from scripts.exam_parser import ExamPaperParser, ExamPaper, ExamQuestion
from scripts.text_chunker import ChineseTextChunker

logger = logging.getLogger(__name__)


class ExamPaperImporter:
    """真题试卷导入器"""

    def __init__(
        self,
        db_path: str = "./data/chroma_db",
        embedding_model: str = "BAAI/bge-base-zh-v1.5",
        device: Optional[str] = None,
        chunk_size: int = 800,
        chunk_overlap: int = 80,
        batch_size: int = 50,
        progress_file: str = "data/exam_import_progress.json",
    ):
        self.db_path = db_path
        self.batch_size = batch_size
        self.progress_file = progress_file

        # 初始化 embedding 模型
        self.embedder = EmbeddingModel(model_name=embedding_model, device=device)

        # 初始化数据库
        self.db = EduRAGDatabase(
            db_path=db_path,
            embedding_model=embedding_model,
            device=device,
            embedder=self.embedder,
        )

        # 初始化解析器和分块器
        self.parser = ExamPaperParser()
        self.chunker = ChineseTextChunker(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )

        # 统计信息
        self.stats = {
            "total_files": 0,
            "parsed_files": 0,
            "skipped_files": 0,
            "failed_files": 0,
            "total_questions": 0,
            "total_chunks": 0,
            "questions_by_type": {},
            "errors": [],
        }

    def scan_source_dir(
        self, source_dir: str, file_types: List[str] = None
    ) -> List[Path]:
        """扫描源目录"""
        file_types = file_types or ["pdf", "docx"]
        root = Path(source_dir)

        if not root.exists():
            logger.error(f"源目录不存在: {source_dir}")
            return []

        files = []
        for ext in file_types:
            files.extend(root.rglob(f"*.{ext}"))

        files.sort(key=lambda f: str(f))
        logger.info(f"扫描到 {len(files)} 个试卷文件")
        return files

    def get_imported_files(self, collection_name: str) -> Set[str]:
        """获取已导入文件集合（断点续传）"""
        progress_path = Path(self.progress_file)
        if progress_path.exists():
            try:
                with open(progress_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return set(data.get(collection_name, {}).get("files", []))
            except Exception as e:
                logger.warning(f"读取进度文件失败: {e}")
        return set()

    def _save_progress(self, collection_name: str, imported_files: Set[str]):
        """保存导入进度"""
        progress_path = Path(self.progress_file)
        progress_path.parent.mkdir(parents=True, exist_ok=True)

        data = {}
        if progress_path.exists():
            try:
                with open(progress_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                data = {}

        data[collection_name] = {
            "files": list(imported_files),
            "stats": self.stats,
            "updated_at": datetime.now().isoformat(),
        }

        with open(progress_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _generate_question_id(
        self, file_path: str, source_root: str, q_number: str, chunk_idx: int
    ) -> str:
        """生成确定性的题目 ID"""
        try:
            rel = str(Path(file_path).relative_to(source_root))
        except ValueError:
            rel = Path(file_path).name
        file_hash = hashlib.md5(rel.encode("utf-8")).hexdigest()[:10]
        return f"exam_{file_hash}_q{q_number}_c{chunk_idx}"

    def process_single_file(
        self, file_path: str, source_root: str
    ) -> List[Dict[str, Any]]:
        """
        处理单个试卷文件：提取 → 解析 → 构建 chunk

        Returns:
            Chunk 字典列表
        """
        # 1. 提取文本
        extractor = get_extractor(file_path)
        if extractor is None:
            return []

        extracted = extractor.extract(file_path)
        if not extracted.extract_success:
            self.stats["errors"].append({
                "file": file_path,
                "error": extracted.error_msg,
            })
            return []

        # 2. 试卷结构化解析
        paper = self.parser.parse(extracted.text, source_file=file_path)
        if not paper.questions:
            self.stats["errors"].append({
                "file": file_path,
                "error": "未能从试卷中解析出任何题目",
            })
            return []

        # 3. 将每道题转为 chunk
        all_chunks = []
        for question in paper.questions:
            chunks = self._question_to_chunks(question, paper, file_path, source_root)
            all_chunks.extend(chunks)

        # 更新统计
        self.stats["total_questions"] += len(paper.questions)
        for q in paper.questions:
            qtype = q.question_type
            self.stats["questions_by_type"][qtype] = \
                self.stats["questions_by_type"].get(qtype, 0) + 1

        return all_chunks

    def _question_to_chunks(
        self,
        question: ExamQuestion,
        paper: ExamPaper,
        file_path: str,
        source_root: str,
    ) -> List[Dict[str, Any]]:
        """
        将单道题目转为可入库的 chunk 列表

        策略：
        - 短题目（<=chunk_size）→ 1 个 chunk
        - 长题目 → 分块，每块带完整元数据
        - 如果有阅读材料，材料和题目分开存储
        """
        # 构建元数据
        base_metadata = {
            "source_file": Path(file_path).name,
            "source_type": "exam_paper",
            "exam_title": paper.title[:100],
            "year": paper.year,
            "exam_region": paper.exam_region,
            "grade_level": paper.grade_level,
            "subject": paper.subject,
            "question_number": question.question_number,
            "question_type": question.question_type,
            "score": question.score,
            "section_name": question.section_name[:80],
            "doc_category": "真题",
            "imported_at": datetime.now().isoformat(),
        }

        # 构建文档文本（用于向量化）
        doc_text = self._build_question_text(question, paper)

        # 文本分块
        chunks = self.chunker.chunk_text(
            doc_text, metadata=base_metadata, source_file=Path(file_path).name
        )

        # 构建结果
        results = []
        for chunk in chunks:
            chunk_id = self._generate_question_id(
                file_path, source_root,
                question.question_number, chunk.chunk_index
            )
            results.append({
                "id": chunk_id,
                "text": chunk.text,
                "metadata": chunk.metadata,
            })

        return results

    def _build_question_text(self, question: ExamQuestion, paper: ExamPaper) -> str:
        """
        构建用于向量化的题目文本

        将元信息嵌入文本开头，增强语义检索效果
        """
        parts = []

        # 前缀：试卷上下文（帮助语义检索）
        context_parts = []
        if paper.year:
            context_parts.append(f"{paper.year}年")
        if paper.exam_region:
            context_parts.append(paper.exam_region)
        if paper.grade_level:
            context_parts.append(paper.grade_level)
        context_prefix = " ".join(context_parts)
        if context_prefix:
            parts.append(f"[{context_prefix} {question.question_type}]")

        # 阅读材料（如果有）
        if question.material:
            parts.append(f"【阅读材料】\n{question.material}")

        # 题目正文
        parts.append(question.question_text)

        # 选项（如果有）
        if question.options:
            parts.append("【选项】")
            parts.extend(question.options)

        # 参考答案（如果有）
        if question.reference_answer:
            parts.append(f"【参考答案】\n{question.reference_answer}")

        return "\n\n".join(parts)

    def import_batch(self, chunks: List[Dict[str, Any]], collection_name: str):
        """批量写入 ChromaDB"""
        if not chunks:
            return

        ids = [c["id"] for c in chunks]
        documents = [c["text"] for c in chunks]
        metadatas = [c["metadata"] for c in chunks]

        # 清理 None 值
        cleaned_metas = []
        for m in metadatas:
            cleaned = {}
            for k, v in m.items():
                if v is not None:
                    cleaned[k] = v
            cleaned_metas.append(cleaned)

        try:
            self.db.add_documents(
                collection_name=collection_name,
                documents=documents,
                metadatas=cleaned_metas,
                ids=ids,
            )
            self.stats["total_chunks"] += len(chunks)
        except Exception as e:
            logger.error(f"批量写入失败: {e}")
            self.stats["errors"].append({
                "action": "batch_write",
                "error": str(e),
                "chunk_count": len(chunks),
            })

    def run(
        self,
        source_dir: str,
        collection_name: str = "exam_papers",
        file_types: Optional[List[str]] = None,
        dry_run: bool = False,
        force: bool = False,
    ):
        """
        执行完整导入流程

        Args:
            source_dir: 试卷文件目录
            collection_name: ChromaDB 集合名称
            file_types: 文件类型过滤
            dry_run: 试运行（只解析不写入）
            force: 强制重新导入
        """
        print(f"\n{'='*60}")
        print(f"  EduRAG 真题库导入工具")
        print(f"{'='*60}")
        print(f"  源目录: {source_dir}")
        print(f"  集合名: {collection_name}")
        print(f"  模式:   {'试运行' if dry_run else '正式导入'}")
        print(f"{'='*60}\n")

        # 1. 扫描文件
        files = self.scan_source_dir(source_dir, file_types)
        self.stats["total_files"] = len(files)

        if not files:
            print("未找到符合条件的文件，退出。")
            return

        # 2. 断点续传检查
        imported_files = set() if force else self.get_imported_files(collection_name)
        if imported_files:
            print(f"发现已导入文件 {len(imported_files)} 个，将跳过已导入文件")

        # 3. 创建集合
        if not dry_run:
            self.db.create_collection(
                collection_name,
                metadata={"hnsw:space": "cosine"},
            )

        # 4. 逐文件处理
        buffer = []
        new_imported = set(imported_files)

        for file_path in tqdm(files, desc="解析试卷", unit="file"):
            filename = file_path.name

            if filename in imported_files and not force:
                self.stats["skipped_files"] += 1
                continue

            # 处理文件
            chunks = self.process_single_file(str(file_path), source_dir)

            if not chunks:
                if filename not in imported_files:
                    self.stats["failed_files"] += 1
                continue

            self.stats["parsed_files"] += 1

            if dry_run:
                self.stats["total_chunks"] += len(chunks)
                new_imported.add(filename)
                continue

            buffer.extend(chunks)
            new_imported.add(filename)

            if len(buffer) >= self.batch_size:
                self.import_batch(buffer, collection_name)
                buffer = []

        # 处理剩余缓冲
        if buffer and not dry_run:
            self.import_batch(buffer, collection_name)

        # 5. 保存进度
        if not dry_run:
            self._save_progress(collection_name, new_imported)

        # 6. 打印摘要
        self.print_summary(dry_run)

    def print_summary(self, dry_run: bool = False):
        """打印导入摘要"""
        s = self.stats
        print(f"\n{'='*60}")
        print(f"  {'试运行' if dry_run else '导入'}完成！")
        print(f"{'='*60}")
        print(f"  总文件数:        {s['total_files']}")
        print(f"  成功解析:        {s['parsed_files']}")
        print(f"  跳过（已导入）:  {s['skipped_files']}")
        print(f"  失败:            {s['failed_files']}")
        print(f"  解析题目总数:    {s['total_questions']}")
        print(f"  生成 Chunk 数:   {s['total_chunks']}")

        if s["questions_by_type"]:
            print(f"\n  题型分布:")
            for qtype, count in sorted(
                s["questions_by_type"].items(), key=lambda x: -x[1]
            ):
                print(f"    {qtype}: {count} 题")

        if s["errors"]:
            print(f"\n  错误记录（{len(s['errors'])} 条）:")
            for err in s["errors"][:10]:
                file_info = err.get("file", err.get("action", ""))
                print(f"    - {file_info}: {err.get('error', '')}")
            if len(s["errors"]) > 10:
                print(f"    ... 还有 {len(s['errors']) - 10} 条错误")

        print(f"{'='*60}\n")


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="EduRAG 真题库导入工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 试运行，查看能解析多少题目
  python scripts/import_exam_papers.py --source D:/真题库 --dry-run

  # 正式导入
  python scripts/import_exam_papers.py --source D:/真题库

  # 指定集合名 + 强制重新导入
  python scripts/import_exam_papers.py --source D:/真题库 --collection gaokao_papers --force
        """,
    )

    parser.add_argument(
        "--source",
        type=str,
        required=True,
        help="试卷文件目录路径",
    )
    parser.add_argument(
        "--collection",
        type=str,
        default="exam_papers",
        help="ChromaDB 集合名称（默认: exam_papers）",
    )
    parser.add_argument(
        "--db-path",
        type=str,
        default="./data/chroma_db",
        help="ChromaDB 存储路径",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=800,
        help="分块大小（字数，默认: 800，试卷文本较长）",
    )
    parser.add_argument(
        "--chunk-overlap",
        type=int,
        default=80,
        help="分块重叠字数（默认: 80）",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=50,
        help="批量写入大小（默认: 50）",
    )
    parser.add_argument(
        "--embedding-model",
        type=str,
        default="BAAI/bge-base-zh-v1.5",
        help="Embedding 模型名",
    )
    parser.add_argument(
        "--device",
        type=str,
        default=None,
        help="计算设备 cpu/cuda",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="试运行，只解析统计不写入",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="强制重新导入",
    )
    parser.add_argument(
        "--file-types",
        type=str,
        default="pdf,docx",
        help="文件类型过滤（默认: pdf,docx）",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="详细日志输出",
    )
    parser.add_argument(
        "--log-file",
        type=str,
        default="logs/exam_import.log",
        help="日志文件路径",
    )

    return parser.parse_args()


def setup_logging(verbose: bool = False, log_file: str = "logs/exam_import.log"):
    """配置日志"""
    log_dir = os.path.dirname(log_file)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)

    level = logging.DEBUG if verbose else logging.INFO
    fmt = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"

    handlers = [logging.StreamHandler(sys.stdout)]
    if log_file:
        handlers.append(logging.FileHandler(log_file, encoding="utf-8"))

    logging.basicConfig(level=level, format=fmt, handlers=handlers)


def main():
    args = parse_args()
    setup_logging(args.verbose, args.log_file)

    file_types = [t.strip() for t in args.file_types.split(",")]

    importer = ExamPaperImporter(
        db_path=args.db_path,
        embedding_model=args.embedding_model,
        device=args.device,
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap,
        batch_size=args.batch_size,
    )

    importer.run(
        source_dir=args.source,
        collection_name=args.collection,
        file_types=file_types,
        dry_run=args.dry_run,
        force=args.force,
    )


if __name__ == "__main__":
    main()
