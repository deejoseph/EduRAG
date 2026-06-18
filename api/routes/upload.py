"""
知识库文档上传 API 路由
支持用户上传 PDF/DOCX 文件到 ChromaDB 知识库
"""

import os
import uuid
import hashlib
import logging
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app

from scripts.doc_extractors import get_extractor
from scripts.metadata_parser import parse_metadata, _extract_title, _classify_category
from scripts.text_chunker import ChineseTextChunker

logger = logging.getLogger(__name__)

upload_bp = Blueprint('upload', __name__)

# 临时上传目录
UPLOAD_TMP = os.path.join(
    os.path.dirname(__file__), '..', '..', 'data', 'upload_tmp'
)


def _ensure_tmp_dir():
    os.makedirs(UPLOAD_TMP, exist_ok=True)


def _get_db():
    return current_app.config['edurag']['db']


def _get_config():
    return current_app.config['edurag']['config']


# ─────────────────────────────────────────────────────────
# POST /upload/files  上传并导入文件
# ─────────────────────────────────────────────────────────
@upload_bp.route('/files', methods=['POST'])
def upload_files():
    """
    上传文件并导入知识库

    multipart/form-data:
        files: 文件列表（PDF/DOCX）
        collection: 目标集合名（默认 chinese_essays）

    Returns:
        每个文件的导入结果（状态、chunk 数、错误信息）
    """
    files = request.files.getlist('files')
    if not files:
        return jsonify({'error': '未提供文件，请选择至少一个 PDF 或 DOCX 文件'}), 400

    collection_name = request.form.get('collection', 'chinese_essays')
    config = _get_config()
    import_cfg = config.get('import', {})

    db = _get_db()
    chunker = ChineseTextChunker(
        chunk_size=import_cfg.get('chunk_size', 500),
        chunk_overlap=import_cfg.get('chunk_overlap', 50),
    )

    _ensure_tmp_dir()

    # 确保集合存在
    db.create_collection(
        collection_name,
        metadata={"hnsw:space": "cosine"},
    )

    results = []
    total_chunks = 0

    for file_storage in files:
        filename = file_storage.filename or 'unknown'
        file_ext = os.path.splitext(filename)[1].lower().lstrip('.')

        # 校验文件类型
        supported = import_cfg.get('supported_types', ['pdf', 'docx'])
        if file_ext not in supported:
            results.append({
                'filename': filename,
                'status': 'error',
                'error': f'不支持的文件格式 .{file_ext}，仅支持 {", ".join(supported)}',
                'chunks': 0,
            })
            continue

        # 保存到临时文件
        tmp_path = os.path.join(UPLOAD_TMP, f"{uuid.uuid4().hex[:8]}_{filename}")
        try:
            file_storage.save(tmp_path)
        except Exception as e:
            results.append({
                'filename': filename,
                'status': 'error',
                'error': f'文件保存失败: {e}',
                'chunks': 0,
            })
            continue

        # 处理文件
        try:
            # 1. 提取文本
            extractor = get_extractor(tmp_path)
            if extractor is None:
                results.append({
                    'filename': filename,
                    'status': 'error',
                    'error': f'无法识别的文件格式',
                    'chunks': 0,
                })
                continue

            extracted = extractor.extract(tmp_path)
            if not extracted.extract_success:
                results.append({
                    'filename': filename,
                    'status': 'error',
                    'error': extracted.error_msg,
                    'chunks': 0,
                })
                continue

            # 2. 解析元数据（使用原始文件名）
            metadata = parse_metadata(tmp_path, UPLOAD_TMP)
            # 覆盖为原始文件名和正确的标题
            metadata['source_file'] = filename
            metadata['source_dir'] = 'upload'
            metadata['title'] = _extract_title(os.path.splitext(filename)[0])
            metadata['doc_category'] = _classify_category(os.path.splitext(filename)[0], 'upload')
            metadata['imported_at'] = datetime.now().isoformat()

            # 3. 文本分块
            chunks = chunker.chunk_extracted_doc(extracted.text, metadata)
            if not chunks:
                results.append({
                    'filename': filename,
                    'status': 'error',
                    'error': '文件内容为空，无法分块',
                    'chunks': 0,
                })
                continue

            # 4. 写入 ChromaDB
            ids = []
            documents = []
            metadatas = []
            for chunk in chunks:
                file_hash = hashlib.md5(filename.encode("utf-8")).hexdigest()[:12]
                chunk_id = f"{file_hash}_{chunk.chunk_index}"
                ids.append(chunk_id)
                documents.append(chunk.text)
                # 清理 None 值
                cleaned_meta = {k: v for k, v in chunk.metadata.items() if v is not None}
                metadatas.append(cleaned_meta)

            db.add_documents(
                collection_name=collection_name,
                documents=documents,
                metadatas=metadatas,
                ids=ids,
            )

            total_chunks += len(chunks)
            results.append({
                'filename': filename,
                'status': 'success',
                'chunks': len(chunks),
                'text_length': len(extracted.text),
                'title': metadata.get('title', ''),
            })
            logger.info(f"文件导入成功: {filename} → {len(chunks)} chunks")

        except Exception as e:
            logger.error(f"文件处理失败 {filename}: {e}")
            results.append({
                'filename': filename,
                'status': 'error',
                'error': str(e),
                'chunks': 0,
            })
        finally:
            # 清理临时文件
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except OSError:
                    pass

    return jsonify({
        'success': True,
        'results': results,
        'total_files': len(files),
        'success_count': sum(1 for r in results if r['status'] == 'success'),
        'total_chunks': total_chunks,
        'collection': collection_name,
    })


# ─────────────────────────────────────────────────────────
# DELETE /upload/collections/<name>  删除集合
# ─────────────────────────────────────────────────────────
@upload_bp.route('/collections/<name>', methods=['DELETE'])
def delete_collection(name):
    """删除指定的知识库集合"""
    # 保护核心集合
    protected = ['chinese_essays', 'exam_papers']
    if name in protected:
        return jsonify({
            'error': f'集合 {name} 是系统核心集合，不允许通过此接口删除',
        }), 403

    db = _get_db()
    ok = db.delete_collection(name)
    if ok:
        return jsonify({'success': True, 'message': f'集合 {name} 已删除'})
    else:
        return jsonify({'error': f'删除集合 {name} 失败'}), 500
