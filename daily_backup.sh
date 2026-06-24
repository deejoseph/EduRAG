#!/bin/bash
# EduRAG 每日工作结束备份脚本
# 使用方法: ./daily_backup.sh

set -e

echo "=========================================="
echo "  EduRAG 每日工作结束备份"
echo "=========================================="
echo ""

# 获取当前日期
DATE=$(date +"%Y%m%d_%H%M%S")
BACKUP_DIR="backup/data_${DATE}"

# 1. 备份 data 目录
echo "📦 步骤 1/3: 备份 data 目录..."
if [ -d "data" ]; then
    mkdir -p "$BACKUP_DIR"
    cp -r data "$BACKUP_DIR/"
    echo "✅ data 目录已备份到: $BACKUP_DIR"
    
    # 计算备份大小
    BACKUP_SIZE=$(du -sh "$BACKUP_DIR" | cut -f1)
    echo "   备份大小: $BACKUP_SIZE"
else
    echo "⚠️  data 目录不存在，跳过"
fi

echo ""

# 2. 导出对话记录
echo "📝 步骤 2/3: 导出对话记录..."
if [ -f "export_conversation_node.js" ]; then
    node export_conversation_node.js
    echo "✅ 对话记录已导出"
elif [ -f "export_conversation_bun.ts" ]; then
    bun run export_conversation_bun.ts
    echo "✅ 对话记录已导出（使用 Bun）"
else
    echo "⚠️  未找到导出脚本，跳过"
fi

echo ""

# 3. 清理旧备份（保留最近7天的备份）
echo "🗑️  步骤 3/3: 清理旧备份..."
cd backup
# 删除超过7天的备份
find . -maxdepth 1 -type d -name "data_*" -mtime +7 -exec rm -rf {} \; 2>/dev/null || true
# 保留最近的3个数据备份
ls -dt data_* 2>/dev/null | tail -n +4 | xargs rm -rf 2>/dev/null || true
cd ..
echo "✅ 旧备份已清理"

echo ""
echo "=========================================="
echo "  ✅ 备份完成！"
echo "=========================================="
echo ""
echo "备份位置: $BACKUP_DIR"
echo ""
echo "提示: 可以安全关闭计算机了"
