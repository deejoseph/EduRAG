"""
EduRAG 知识库批量导入脚本
支持 PDF/DOCX 文档提取、中文分块、元数据解析、断点续传
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
from scripts.metadata_parser import parse_metadata
from scripts.text_chunker import ChineseTextChunker

logger = logging.getLogger(__name__)


class KnowledgeBaseImporter:
    """知识库批量导入器"""

    def __init__(
        self,
        db_path: str = "./data/chroma_db",
        embedding_model: str = "BAAI/bge-base-zh-v1.5",
        device: Optional[str] = None,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        batch_size: int = 50,
        progress_file: str = "data/import_progress.json",
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

        # 初始化分块器
        self.chunker = ChineseTextChunker(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )

        # 统计信息
        self.stats = {
            "total_files": 0,
            "skipped_files": 0,
            "success_files": 0,
            "failed_files": 0,
            "total_chunks": 0,
            "errors": [],
        }

    def scan_source_dir(
        self, source_dir: str, file_types: List[str] = None
    ) -> List[Path]:
        """
        扫描源目录，返回符合条件的文件路径列表

        Args:
            source_dir: 源目录路径
            file_types: 文件类型过滤（如 ["pdf", "docx"]）

        Returns:
            文件路径列表
        """
        file_types = file_types or ["pdf", "docx"]
        root = Path(source_dir)

        if not root.exists():
            logger.error(f"源目录不存在: {source_dir}")
            return []

        files = []
        for ext in file_types:
            files.extend(root.rglob(f"*.{ext}"))

        # 按文件名排序保证确定性
        files.sort(key=lambda f: str(f))
        logger.info(f"扫描到 {len(files)} 个文件（类型: {', '.join(file_types)}）")
        return files

    def get_imported_files(self, collection_name: str) -> Set[str]:
        """
        获取已导入的文件集合（用于断点续传）

        Args:
            collection_name: 集合名称

        Returns:
            已导入的文件名集合
        """
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
            "updated_at": datetime.now().isoformat(),
        }

        with open(progress_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _generate_chunk_id(self, file_path: str, source_root: str, chunk_index: int) -> str:
        """生成确定性的文档 ID"""
        try:
            rel = str(Path(file_path).relative_to(source_root))
        except ValueError:
            rel = Path(file_path).name
        file_hash = hashlib.md5(rel.encode("utf-8")).hexdigest()[:12]
        return f"{file_hash}_{chunk_index}"

    def process_single_file(
        self, file_path: str, source_root: str
    ) -> List[Dict[str, Any]]:
        """
        处理单个文件：提取→元数据→分块

        Args:
            file_path: 文件路径
            source_root: 源目录根路径

        Returns:
            Chunk 字典列表，每项包含 id, text, metadata
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

        # 2. 提取元数据
        metadata = parse_metadata(file_path, source_root)

        # 3. 文本分块
        chunks = self.chunker.chunk_extracted_doc(extracted.text, metadata)

        # 4. 构建结果
        results = []
        for chunk in chunks:
            chunk_id = self._generate_chunk_id(
                file_path, source_root, chunk.chunk_index
            )
            results.append({
                "id": chunk_id,
                "text": chunk.text,
                "metadata": chunk.metadata,
            })

        return results

    def import_batch(
        self,
        chunks: List[Dict[str, Any]],
        collection_name: str,
    ):
        """
        批量写入 ChromaDB

        Args:
            chunks: Chunk 字典列表
            collection_name: 集合名称
        """
        if not chunks:
            return

        ids = [c["id"] for c in chunks]
        documents = [c["text"] for c in chunks]
        metadatas = [c["metadata"] for c in chunks]

        # ChromaDB 要求 metadata 值不能为 None，需要清理
        cleaned_metas = []
        for m in metadatas:
            cleaned = {k: v for k, v in m.items() if v is not None}
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
        collection_name: str = "chinese_essays",
        file_types: Optional[List[str]] = None,
        dry_run: bool = False,
        force: bool = False,
    ):
        """
        执行完整导入流程

        Args:
            source_dir: 源文件目录
            collection_name: ChromaDB 集合名称
            file_types: 文件类型过滤
            dry_run: 试运行模式（只扫描不写入）
            force: 强制重新导入（忽略断点续传）
        """
        print(f"\n{'='*60}")
        print(f"  EduRAG 知识库导入工具")
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

        # 3. 创建集合（非试运行）
        if not dry_run:
            self.db.create_collection(
                collection_name,
                metadata={"hnsw:space": "cosine"},
            )

        # 4. 逐文件处理
        buffer = []
        new_imported = set(imported_files)

        for file_path in tqdm(files, desc="处理文件", unit="file"):
            filename = file_path.name

            # 跳过已导入
            if filename in imported_files and not force:
                self.stats["skipped_files"] += 1
                continue

            # 处理文件
            chunks = self.process_single_file(str(file_path), source_dir)

            if not chunks:
                if filename not in imported_files:
                    self.stats["failed_files"] += 1
                continue

            if dry_run:
                self.stats["success_files"] += 1
                self.stats["total_chunks"] += len(chunks)
                new_imported.add(filename)
                continue

            # 加入缓冲区
            buffer.extend(chunks)
            new_imported.add(filename)
            self.stats["success_files"] += 1

            # 缓冲区满则批量写入
            if len(buffer) >= self.batch_size:
                self.import_batch(buffer, collection_name)
                buffer = []

        # 处理剩余缓冲区
        if buffer and not dry_run:
            self.import_batch(buffer, collection_name)
            buffer = []

        # 5. 保存进度
        if not dry_run:
            self._save_progress(collection_name, new_imported)

        # 6. 打印统计摘要
        self.print_summary(dry_run)

    def print_summary(self, dry_run: bool = False):
        """打印导入统计摘要"""
        s = self.stats
        print(f"\n{'='*60}")
        print(f"  {'试运行' if dry_run else '导入'}完成！统计摘要：")
        print(f"{'='*60}")
        print(f"  总文件数:     {s['total_files']}")
        print(f"  成功处理:     {s['success_files']}")
        print(f"  跳过（已导入）: {s['skipped_files']}")
        print(f"  失败:         {s['failed_files']}")
        print(f"  总 Chunk 数:  {s['total_chunks']}")

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
        description="EduRAG 知识库批量导入工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--source",
        type=str,
        default=r"D:\BaiduNetdiskDownload\2025全国高考满分作文电子版历年语文写作优秀范文1000篇学习资料",
        help="源文件目录路径",
    )
    parser.add_argument(
        "--collection",
        type=str,
        default="chinese_essays",
        help="ChromaDB 集合名称（默认: chinese_essays）",
    )
    parser.add_argument(
        "--db-path",
        type=str,
        default="./data/chroma_db",
        help="ChromaDB 存储路径（默认: ./data/chroma_db）",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=500,
        help="分块大小（字数，默认: 500）",
    )
    parser.add_argument(
        "--chunk-overlap",
        type=int,
        default=50,
        help="分块重叠字数（默认: 50）",
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
        help="Embedding 模型名（默认: BAAI/bge-base-zh-v1.5）",
    )
    parser.add_argument(
        "--device",
        type=str,
        default=None,
        help="计算设备 cpu/cuda（默认: 自动检测）",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="试运行模式，只扫描统计不写入",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="强制重新导入（忽略断点续传）",
    )
    parser.add_argument(
        "--file-types",
        type=str,
        default="pdf,docx",
        help="文件类型过滤，逗号分隔（默认: pdf,docx）",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="详细日志输出",
    )
    parser.add_argument(
        "--log-file",
        type=str,
        default="logs/import.log",
        help="日志文件路径（默认: logs/import.log）",
    )

    return parser.parse_args()


def setup_logging(verbose: bool = False, log_file: str = "logs/import.log"):
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

    importer = KnowledgeBaseImporter(
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
