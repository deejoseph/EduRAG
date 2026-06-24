"""简单导出对话记录"""
import json
from pathlib import Path
from datetime import datetime

# 对话记录文件路径
jsonl_path = Path(r"C:\Users\deejo\.qoder-cn\cache\projects\EduRAG-8fad6596\conversation-history\task-327\task-327.jsonl")

if not jsonl_path.exists():
    print(f"对话记录文件不存在: {jsonl_path}")
    # 尝试查找其他位置
    alt_path = Path("conversation-history/task-327/task-327.jsonl")
    if alt_path.exists():
        jsonl_path = alt_path
        print(f"使用备用路径: {jsonl_path}")
    else:
        print("未找到对话记录文件")
        exit(1)

print(f"读取对话记录: {jsonl_path}")

# 读取消息
messages = []
with open(jsonl_path, 'r', encoding='utf-8') as f:
    for line_num, line in enumerate(f, 1):
        line = line.strip()
        if line:
            try:
                data = json.loads(line)
                messages.append(data)
            except Exception as e:
                print(f"第{line_num}行解析失败: {e}")

print(f"共读取 {len(messages)} 条消息")

# 生成Markdown
output_lines = []
output_lines.append("# EduRAG 项目开发对话记录\n")
output_lines.append(f"**导出时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
output_lines.append(f"**总消息数**: {len(messages)}\n")
output_lines.append("---\n")

user_count = 0
assistant_count = 0

for i, msg in enumerate(messages, 1):
    role = msg.get("role", "unknown")
    
    if role == "user":
        user_count += 1
        output_lines.append(f"\n## 👤 用户消息 #{user_count}\n")
    elif role == "assistant":
        assistant_count += 1
        output_lines.append(f"\n## 🤖 AI助手消息 #{assistant_count}\n")
    
    # 提取文本内容
    content_blocks = msg.get("message", {}).get("content", [])
    
    for block in content_blocks:
        if isinstance(block, dict):
            if block.get("type") == "text":
                text = block.get("text", "")
                if text:
                    output_lines.append(text)
                    output_lines.append("\n")
            
            elif block.get("type") == "tool_use":
                tool_name = block.get("name", "")
                output_lines.append(f"\n```python\n# 工具调用: {tool_name}\n```\n")
            
            elif block.get("type") == "tool_result":
                output_lines.append("\n```output\n[工具执行结果]\n```\n")
        
        elif isinstance(block, str):
            output_lines.append(block)
            output_lines.append("\n")
    
    output_lines.append("\n---\n")

# 添加统计
output_lines.append("\n## 📊 对话统计\n\n")
output_lines.append(f"- 用户消息: {user_count} 条\n")
output_lines.append(f"- AI助手消息: {assistant_count} 条\n")
output_lines.append(f"- 总消息数: {len(messages)} 条\n")

# 写入文件
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
output_path = Path(f"docs/conversation_{timestamp}.md")
output_path.parent.mkdir(parents=True, exist_ok=True)

with open(output_path, 'w', encoding='utf-8') as f:
    f.write(''.join(output_lines))

print(f"\n✅ 对话记录已导出到: {output_path}")
print(f"📄 文件大小: {output_path.stat().st_size / 1024:.2f} KB")
