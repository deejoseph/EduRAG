"""
导出 Qoder 对话记录为 Markdown 格式
用于写书时保留开发过程记录
"""

import json
from pathlib import Path
from datetime import datetime


def export_conversation_to_markdown(jsonl_path: str, output_path: str = None):
    """
    将 JSONL 格式的对话记录转换为 Markdown
    
    Args:
        jsonl_path: JSONL 文件路径
        output_path: 输出 Markdown 文件路径（可选）
    """
    # 读取对话记录
    conversations = []
    with open(jsonl_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                try:
                    msg = json.loads(line)
                    conversations.append(msg)
                except json.JSONDecodeError:
                    continue
    
    if not conversations:
        print("❌ 对话记录为空")
        return
    
    print(f"✅ 共读取 {len(conversations)} 条对话记录")
    
    # 生成 Markdown 内容
    lines = []
    
    # 标题和元数据
    task_name = Path(jsonl_path).parent.name
    lines.append(f"# EduRAG 项目开发对话记录\n")
    lines.append(f"**任务ID**: {task_name}\n")
    lines.append(f"**导出时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    lines.append(f"**对话条数**: {len(conversations)}\n")
    lines.append("---\n\n")
    
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
        
        lines.append(f"## 对话 {i} - {role_display}\n\n")
        
        # 提取文本内容
        text_content = ""
        has_code = False
        
        for block in content_blocks:
            if isinstance(block, dict):
                if block.get('type') == 'text':
                    text_content += block.get('text', '')
                elif block.get('type') == 'code':
                    has_code = True
                    lang = block.get('language', '')
                    code = block.get('code', '')
                    text_content += f"\n\n```{lang}\n{code}\n```\n\n"
            elif isinstance(block, str):
                text_content += block
        
        if text_content:
            lines.append(f"{text_content}\n\n")
        
        lines.append("---\n\n")
        
        # 每 50 条显示进度
        if i % 50 == 0:
            print(f"  处理进度: {i}/{len(conversations)}")
    
    # 写入文件
    if output_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"conversation_{task_name}_{timestamp}.md"
    
    md_content = '\n'.join(lines)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(md_content)
    
    print(f"\n✅ 导出成功！")
    print(f"📄 文件路径: {output_path}")
    print(f"📊 文件大小: {len(md_content):,} 字符")
    

if __name__ == '__main__':
    import sys
    
    # 支持命令行参数指定目录
    if len(sys.argv) > 1:
        qoder_base = Path(sys.argv[1])
    else:
        # 默认使用国际版 Qoder 目录
        qoder_base = Path.home() / '.qoder' / 'cache' / 'projects'
    
    print(f"📂 搜索目录: {qoder_base}")
    print()
    
    # 查找 EduRAG 项目目录
    project_dirs = list(qoder_base.glob('EduRAG-*'))
    if not project_dirs:
        print("❌ 未找到 EduRAG 项目目录")
        exit(1)
    
    # 使用第一个匹配的项目
    project_dir = project_dirs[0]
    conversation_dir = project_dir / 'conversation-history'
    
    if not conversation_dir.exists():
        print("❌ 对话历史目录不存在")
        exit(1)
    
    # 查找所有任务
    task_dirs = [d for d in conversation_dir.iterdir() if d.is_dir() and d.name.startswith('task-')]
    if not task_dirs:
        print("❌ 未找到任何任务对话")
        exit(1)
    
    print(f"找到 {len(task_dirs)} 个任务:")
    for task_dir in task_dirs:
        print(f"  - {task_dir.name}")
    
    # 处理每个任务（按最后修改时间排序）
    for task_dir in sorted(task_dirs, key=lambda x: x.stat().st_mtime):
        print(f"\n{'='*60}")
        print(f"处理任务: {task_dir.name}")
        print('='*60)
        
        # 查找 JSONL 文件
        jsonl_files = list(task_dir.glob('*.jsonl'))
        if not jsonl_files:
            print(f"  ⚠️  任务 {task_dir.name} 中没有对话记录")
            continue
        
        jsonl_file = jsonl_files[0]
        print(f"  📄 文件: {jsonl_file.name}")
        
        # 导出
        try:
            export_conversation_to_markdown(str(jsonl_file))
        except Exception as e:
            print(f"  ❌ 导出失败: {e}")
    
    print("\n" + "="*60)
    print("✅ 所有任务导出完成！")
    print("="*60)
