/**
 * 使用 Bun 导出 Qoder 对话记录为 Markdown
 * 
 * 使用方法:
 *   bun run export_conversation.ts
 *   或
 *   bunx tsx export_conversation.ts
 */

import { readFileSync, writeFileSync, mkdirSync, existsSync } from "fs";
import { join, dirname } from "path";

interface MessageBlock {
  type: string;
  text?: string;
  image_url?: { url: string };
  name?: string;
  input?: any;
  content?: any;
}

interface Message {
  role: string;
  message: {
    content: MessageBlock[];
  };
}

/**
 * 检测文件编码并读取内容
 * 由于 JSONL 文件可能是 UTF-8 或其他编码，我们尝试多种方法
 */
function readJsonlFile(filePath: string): string[] {
  const lines: string[] = [];
  
  try {
    // 首先尝试直接读取为 UTF-8
    const content = readFileSync(filePath, 'utf-8');
    lines.push(...content.split('\n').filter(line => line.trim()));
  } catch (error) {
    console.error(`❌ 读取文件失败: ${error}`);
    return [];
  }
  
  return lines;
}

/**
 * 解析单行 JSONL 数据
 */
function parseLine(line: string): Message | null {
  try {
    return JSON.parse(line.trim());
  } catch (error) {
    // 跳过空行或无效行
    if (line.trim()) {
      console.warn(`⚠️  解析失败: ${line.substring(0, 50)}...`);
    }
    return null;
  }
}

/**
 * 将消息转换为 Markdown 格式
 */
function convertToMarkdown(messages: Message[]): string {
  const output: string[] = [];
  
  // 标题和元信息
  output.push('# EduRAG 项目开发对话记录\n');
  output.push(`**导出时间**: ${new Date().toLocaleString('zh-CN')}\n`);
  output.push(`**总消息数**: ${messages.length}\n`);
  output.push('---\n');
  
  let userCount = 0;
  let assistantCount = 0;
  
  messages.forEach((msg, index) => {
    const role = msg.role;
    
    // 添加角色标题
    if (role === 'user') {
      userCount++;
      output.push(`\n## 👤 用户消息 #${userCount}\n`);
    } else if (role === 'assistant') {
      assistantCount++;
      output.push(`\n## 🤖 AI助手消息 #${assistantCount}\n`);
    } else {
      output.push(`\n## ${role}\n`);
    }
    
    // 处理消息内容块
    msg.message.content.forEach((block) => {
      switch (block.type) {
        case 'text':
          if (block.text) {
            output.push(block.text);
            output.push('\n');
          }
          break;
          
        case 'image':
          if (block.image_url?.url) {
            output.push(`\n![Image](${block.image_url.url})\n`);
          }
          break;
          
        case 'tool_use':
          output.push(`\n\`\`\`python\n# 工具调用: ${block.name || 'unknown'}`);
          if (block.input) {
            output.push(`# 参数:\n# ${JSON.stringify(block.input, null, 2)}`);
          }
          output.push('```\n');
          break;
          
        case 'tool_result':
          output.push('\n```output');
          if (block.content) {
            const contentStr = typeof block.content === 'string' 
              ? block.content 
              : JSON.stringify(block.content);
            // 限制输出长度
            const preview = contentStr.substring(0, 1000);
            output.push(preview);
            if (contentStr.length > 1000) {
              output.push(`\n... (剩余${contentStr.length - 1000}字符)`);
            }
          } else {
            output.push('[工具执行完成]');
          }
          output.push('\n```\n');
          break;
          
        default:
          // 处理字符串类型的块
          if (typeof block === 'string') {
            output.push(block);
            output.push('\n');
          }
      }
    });
    
    output.push('\n---\n');
  });
  
  // 添加统计信息
  output.push('\n## 📊 对话统计\n\n');
  output.push(`- 用户消息: ${userCount} 条\n`);
  output.push(`- AI助手消息: ${assistantCount} 条\n`);
  output.push(`- 总消息数: ${messages.length} 条\n`);
  
  return output.join('');
}

/**
 * 主函数
 */
function main() {
  console.log('🚀 EduRAG 对话记录导出工具 (Bun 版本)\n');
  
  // 对话记录文件路径
  const jsonlPath = 'C:\\Users\\deejo\\.qoder-cn\\cache\\projects\\EduRAG-8fad6596\\conversation-history\\task-327\\task-327.jsonl';
  
  // 检查文件是否存在
  if (!existsSync(jsonlPath)) {
    console.error(`❌ 对话记录文件不存在: ${jsonlPath}`);
    console.log('\n💡 提示: 请检查文件路径是否正确');
    process.exit(1);
  }
  
  console.log(`📖 读取对话记录: ${jsonlPath}`);
  
  // 读取文件
  const lines = readJsonlFile(jsonlPath);
  console.log(`✅ 共读取 ${lines.length} 行`);
  
  // 解析消息
  const messages: Message[] = [];
  for (const line of lines) {
    const msg = parseLine(line);
    if (msg) {
      messages.push(msg);
    }
  }
  
  console.log(`✅ 成功解析 ${messages.length} 条消息\n`);
  
  // 转换为 Markdown
  console.log('📝 转换为 Markdown 格式...');
  const markdown = convertToMarkdown(messages);
  
  // 创建输出目录
  const outputDir = 'docs';
  if (!existsSync(outputDir)) {
    mkdirSync(outputDir, { recursive: true });
    console.log(`✅ 创建输出目录: ${outputDir}`);
  }
  
  // 生成输出文件名（带时间戳）
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-').split('T')[0] + '_' + 
                   new Date().toTimeString().split(' ')[0].replace(/:/g, '');
  const outputPath = join(outputDir, `conversation_${timestamp}.md`);
  
  // 写入文件
  console.log(`💾 保存到: ${outputPath}`);
  writeFileSync(outputPath, markdown, 'utf-8');
  
  // 计算文件大小
  const fileSize = Buffer.byteLength(markdown, 'utf-8');
  const fileSizeKB = (fileSize / 1024).toFixed(2);
  
  console.log(`\n✅ 导出完成！`);
  console.log(`📄 文件大小: ${fileSizeKB} KB`);
  console.log(`📍 保存位置: ${outputPath}`);
  console.log(`\n🎉 现在可以在写书时使用这个 Markdown 文件了！`);
}

// 运行主函数
main();
