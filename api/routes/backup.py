"""
数据备份和导出 API
"""

import os
import json
import shutil
import logging
from datetime import datetime
from pathlib import Path
from flask import Blueprint, request, jsonify, current_app, send_file

logger = logging.getLogger(__name__)

backup_bp = Blueprint('backup', __name__)


@backup_bp.route('/database', methods=['POST'])
def backup_database():
    """
    备份 ChromaDB 向量数据库
    
    Request Body:
        backup_name: 备份名称（可选，默认使用时间戳）
    
    Returns:
        备份结果，包含备份路径和大小
    """
    try:
        # 获取配置
        config = current_app.config['edurag']['config']
        db_path = config.get('chromadb', {}).get('path', './data/chroma_db')
        
        # 验证路径存在
        chroma_path = Path(db_path)
        if not chroma_path.exists():
            return jsonify({'error': f'ChromaDB目录不存在: {db_path}'}), 404
        
        # 生成备份目录
        backup_root = Path('backup')
        backup_root.mkdir(exist_ok=True)
        
        backup_name = request.get_json().get('backup_name', '') if request.get_json() else ''
        if not backup_name:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"chroma_db_{timestamp}"
        
        backup_dest = backup_root / backup_name
        
        # 检查是否已存在
        if backup_dest.exists():
            return jsonify({'error': f'备份已存在: {backup_name}'}), 409
        
        logger.info(f"开始备份 ChromaDB: {chroma_path} -> {backup_dest}")
        
        # 执行备份
        shutil.copytree(chroma_path, backup_dest)
        
        # 计算备份大小
        total_size = sum(f.stat().st_size for f in backup_dest.rglob('*') if f.is_file())
        size_mb = total_size / (1024 * 1024)
        
        # 清理旧备份（保留最近5个）
        old_backups = sorted(backup_root.glob("chroma_db_*"))
        if len(old_backups) > 5:
            for old in old_backups[:-5]:
                logger.info(f"删除旧备份: {old}")
                shutil.rmtree(old)
        
        logger.info(f"备份完成: {backup_dest}, 大小: {size_mb:.2f} MB")
        
        return jsonify({
            'success': True,
            'message': f'备份成功',
            'backup_path': str(backup_dest),
            'backup_name': backup_name,
            'size_mb': round(size_mb, 2),
            'timestamp': datetime.now().isoformat(),
        })
    
    except Exception as e:
        logger.error(f"备份失败: {e}", exc_info=True)
        return jsonify({'error': f'备份失败: {str(e)}'}), 500


@backup_bp.route('/list', methods=['GET'])
def list_backups():
    """
    列出所有备份
    
    Returns:
        备份列表
    """
    try:
        backup_root = Path('backup')
        if not backup_root.exists():
            return jsonify({'success': True, 'backups': []})
        
        backups = []
        for backup_dir in sorted(backup_root.iterdir()):
            if backup_dir.is_dir() and backup_dir.name.startswith('chroma_db_'):
                # 计算大小
                total_size = sum(f.stat().st_size for f in backup_dir.rglob('*') if f.is_file())
                size_mb = total_size / (1024 * 1024)
                
                # 提取时间戳
                timestamp_str = backup_dir.name.replace('chroma_db_', '')
                try:
                    timestamp = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                    created_at = timestamp.isoformat()
                except:
                    created_at = '未知'
                
                backups.append({
                    'name': backup_dir.name,
                    'path': str(backup_dir),
                    'size_mb': round(size_mb, 2),
                    'created_at': created_at,
                })
        
        return jsonify({
            'success': True,
            'backups': backups,
            'total': len(backups),
        })
    
    except Exception as e:
        logger.error(f"列出备份失败: {e}", exc_info=True)
        return jsonify({'error': f'获取备份列表失败: {str(e)}'}), 500


@backup_bp.route('/delete/<backup_name>', methods=['DELETE'])
def delete_backup(backup_name):
    """
    删除指定备份
    
    Args:
        backup_name: 备份名称
    
    Returns:
        删除结果
    """
    try:
        backup_path = Path('backup') / backup_name
        
        if not backup_path.exists():
            return jsonify({'error': f'备份不存在: {backup_name}'}), 404
        
        # 安全检查：确保在 backup 目录下
        if not str(backup_path.resolve()).startswith(str(Path('backup').resolve())):
            return jsonify({'error': '非法的备份路径'}), 403
        
        shutil.rmtree(backup_path)
        logger.info(f"删除备份: {backup_name}")
        
        return jsonify({
            'success': True,
            'message': f'备份 {backup_name} 已删除',
        })
    
    except Exception as e:
        logger.error(f"删除备份失败: {e}", exc_info=True)
        return jsonify({'error': f'删除失败: {str(e)}'}), 500


@backup_bp.route('/export-conversation', methods=['POST'])
def export_conversation():
    """
    导出 Qoder 对话记录为 Markdown 格式
    
    Request Body:
        task_id: 任务ID（可选，默认最新）
        output_format: 输出格式（markdown/json，默认 markdown）
    
    Returns:
        导出文件下载
    """
    try:
        # Qoder 对话记录路径（Windows）
        qoder_base = Path.home() / '.qoder-cn' / 'cache' / 'projects'
        
        # 查找 EduRAG 项目目录
        project_dirs = list(qoder_base.glob('EduRAG-*'))
        if not project_dirs:
            return jsonify({'error': '未找到 EduRAG 项目目录'}), 404
        
        # 使用第一个匹配的项目
        project_dir = project_dirs[0]
        conversation_dir = project_dir / 'conversation-history'
        
        if not conversation_dir.exists():
            return jsonify({'error': '对话历史目录不存在'}), 404
        
        # 查找所有任务
        task_dirs = [d for d in conversation_dir.iterdir() if d.is_dir() and d.name.startswith('task-')]
        if not task_dirs:
            return jsonify({'error': '未找到任何任务对话'}), 404
        
        # 按任务ID排序，获取最新的
        task_dirs.sort(key=lambda x: int(x.name.replace('task-', '')), reverse=True)
        
        # 如果指定了 task_id，使用指定的
        data = request.get_json() or {}
        task_id = data.get('task_id')
        
        if task_id:
            target_task = conversation_dir / f'task-{task_id}'
            if not target_task.exists():
                return jsonify({'error': f'任务 {task_id} 不存在'}), 404
            selected_task = target_task
        else:
            selected_task = task_dirs[0]
        
        # 查找 JSONL 文件
        jsonl_files = list(selected_task.glob('*.jsonl'))
        if not jsonl_files:
            return jsonify({'error': f'任务 {selected_task.name} 中没有对话记录'}), 404
        
        jsonl_file = jsonl_files[0]
        
        # 读取对话记录
        conversations = []
        with open(jsonl_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    try:
                        msg = json.loads(line)
                        conversations.append(msg)
                    except json.JSONDecodeError:
                        continue
        
        if not conversations:
            return jsonify({'error': '对话记录为空'}), 404
        
        # 转换为 Markdown 格式
        output_format = data.get('output_format', 'markdown')
        
        if output_format == 'markdown':
            md_content = _convert_to_markdown(conversations, selected_task.name)
            
            # 保存到临时文件
            tmp_dir = Path(__file__).parent.parent / 'data' / 'upload_tmp'
            tmp_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"conversation_{selected_task.name}_{timestamp}.md"
            tmp_file = tmp_dir / filename
            
            with open(tmp_file, 'w', encoding='utf-8') as f:
                f.write(md_content)
            
            logger.info(f"导出对话记录: {filename}, 共 {len(conversations)} 条消息")
            
            # 返回文件下载
            return send_file(
                str(tmp_file),
                mimetype='text/markdown',
                as_attachment=True,
                download_name=filename,
            )
        
        elif output_format == 'json':
            # 直接返回 JSON
            return jsonify({
                'success': True,
                'task_id': selected_task.name,
                'message_count': len(conversations),
                'conversations': conversations,
            })
        
        else:
            return jsonify({'error': f'不支持的输出格式: {output_format}'}), 400
    
    except Exception as e:
        logger.error(f"导出对话记录失败: {e}", exc_info=True)
        return jsonify({'error': f'导出失败: {str(e)}'}), 500


def _convert_to_markdown(conversations: list, task_name: str) -> str:
    """
    将对话记录转换为 Markdown 格式
    
    Args:
        conversations: 对话列表
        task_name: 任务名称
    
    Returns:
        Markdown 格式的字符串
    """
    lines = []
    
    # 标题
    lines.append(f"# EduRAG 对话记录\n")
    lines.append(f"**任务ID**: {task_name}\n")
    lines.append(f"**导出时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    lines.append(f"**对话条数**: {len(conversations)}\n")
    lines.append("---\n")
    
    # 遍历对话
    for i, msg in enumerate(conversations, 1):
        role = msg.get('role', 'unknown')
        message_data = msg.get('message', {})
        content_blocks = message_data.get('content', [])
        
        # 角色映射
        role_display = {
            'user': '👤 用户',
            'assistant': '🤖 助手',
            'system': '⚙️ 系统',
        }.get(role, role)
        
        lines.append(f"## 对话 {i} - {role_display}\n")
        
        # 提取文本内容
        text_content = ""
        for block in content_blocks:
            if isinstance(block, dict):
                if block.get('type') == 'text':
                    text_content += block.get('text', '')
            elif isinstance(block, str):
                text_content += block
        
        if text_content:
            lines.append(f"{text_content}\n")
        
        lines.append("---\n")
    
    return '\n'.join(lines)
