"""
导出对话记录为Markdown格式
用于写书时参考
"""

import json
from datetime import datetime
from pathlib import Path


def export_conversation_to_markdown(jsonl_path: str, output_path: str):
    """将JSONL格式的对话记录导出为Markdown"""
    
    # 读取所有对话记录
    messages = []
    with open(jsonl_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    data = json.loads(line)
                    messages.append(data)
                except json.JSONDecodeError:
                    continue
    
    print(f"读取到 {len(messages)} 条消息")
    
    # 生成Markdown
    markdown_content = []
    markdown_content.append("# EduRAG 项目开发对话记录\n")
    markdown_content.append(f"**导出时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    markdown_content.append(f"**总消息数**: {len(messages)}\n")
    markdown_content.append("---\n\n")
    
    current_role = None
    message_count = {"user": 0, "assistant": 0}
    
    for msg in messages:
        role = msg.get("role", "unknown")
        message_count[role] = message_count.get(role, 0) + 1
        
        # 添加角色标题
        if role != current_role:
            if role == "user":
                markdown_content.append("\n## 👤 用户\n")
            elif role == "assistant":
                markdown_content.append("\n## 🤖 AI助手\n")
            else:
                markdown_content.append(f"\n## {role}\n")
            current_role = role
        
        # 提取消息内容
        content_blocks = msg.get("message", {}).get("content", [])
        
        for block in content_blocks:
            if isinstance(block, dict):
                # 文本内容
                if block.get("type") == "text":
                    text = block.get("text", "")
                    if text:
                        markdown_content.append(text)
                        markdown_content.append("\n")
                
                # 图片内容
                elif block.get("type") == "image":
                    image_url = block.get("image_url", {}).get("url", "")
                    if image_url:
                        markdown_content.append(f"\n![Image]({image_url})\n")
                
                # 工具调用
                elif block.get("type") == "tool_use":
                    tool_name = block.get("name", "")
                    tool_input = block.get("input", {})
                    markdown_content.append(f"\n```python\n# 工具调用: {tool_name}\n")
                    if tool_input:
                        markdown_content.append(f"# 参数:\n# {json.dumps(tool_input, ensure_ascii=False, indent=2)}\n")
                    markdown_content.append("```\n")
                
                # 工具结果
                elif block.get("type") == "tool_result":
                    result_content = block.get("content", "")
                    if result_content:
                        markdown_content.append("\n```output\n")
                        # 如果内容太长，截取前500字符
                        if isinstance(result_content, str):
                            preview = result_content[:500]
                            markdown_content.append(preview)
                            if len(result_content) > 500:
                                markdown_content.append(f"\n... (剩余{len(result_content) - 500}字符)")
                        else:
                            markdown_content.append(str(result_content))
                        markdown_content.append("\n```\n")
            
            elif isinstance(block, str):
                markdown_content.append(block)
                markdown_content.append("\n")
        
        # 添加分隔线
        markdown_content.append("\n---\n")
    
    # 添加统计信息
    markdown_content.append("\n## 📊 对话统计\n\n")
    markdown_content.append(f"- 用户消息: {message_count.get('user', 0)} 条\n")
    markdown_content.append(f"- AI助手消息: {message_count.get('assistant', 0)} 条\n")
    markdown_content.append(f"- 总消息数: {len(messages)} 条\n")
    
    # 写入文件
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(''.join(markdown_content))
    
    print(f"对话记录已导出到: {output_path}")
    print(f"Markdown文件大小: {output_file.stat().st_size / 1024:.2f} KB")


if __name__ == "__main__":
    # 查找最近的对话记录文件
    conversation_dir = Path("conversation-history")
    
    if conversation_dir.exists():
        # 查找所有task目录
        task_dirs = list(conversation_dir.glob("task-*"))
        
        if task_dirs:
            # 选择最近的task目录
            latest_task = sorted(task_dirs)[-1]
            jsonl_file = latest_task / "task.jsonl"
            
            if jsonl_file.exists():
                print(f"找到对话记录: {jsonl_file}")
                
                # 生成输出文件名（包含时间戳）
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_file = f"docs/conversation_export_{timestamp}.md"
                
                export_conversation_to_markdown(str(jsonl_file), output_file)
            else:
                print(f"未找到对话记录文件: {jsonl_file}")
        else:
            print("未找到任何task目录")
    else:
        print(f"对话记录目录不存在: {conversation_dir}")
        print("请检查项目结构")
