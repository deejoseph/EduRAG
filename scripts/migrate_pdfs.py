"""
PDF范文迁移脚本
将外部目录的PDF文件复制到项目 data/docs/pdfs 目录
"""
import os
import sys
import shutil
from pathlib import Path

# 设置标准输出编码为 UTF-8
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 源目录（外部目录）
SOURCE_DIR = r"D:\BaiduNetdiskDownload\2025全国高考满分作文电子版历年语文写作优秀范文1000篇学习资料"

# 目标目录（项目内）
TARGET_DIR = Path(__file__).parent.parent / "data" / "docs" / "pdfs"

def migrate_pdfs():
    """迁移所有PDF文件到项目目录"""
    if not os.path.exists(SOURCE_DIR):
        print(f"❌ 源目录不存在: {SOURCE_DIR}")
        return False

    # 确保目标目录存在
    TARGET_DIR.mkdir(parents=True, exist_ok=True)

    # 统计信息
    total_count = 0
    success_count = 0
    skip_count = 0

    print(f"📂 开始迁移PDF文件...")
    print(f"   源目录: {SOURCE_DIR}")
    print(f"   目标目录: {TARGET_DIR}")
    print()

    # 递归遍历源目录
    for root, dirs, files in os.walk(SOURCE_DIR):
        for filename in files:
            if filename.lower().endswith('.pdf'):
                total_count += 1
                source_file = os.path.join(root, filename)

                # 构建相对路径（保持子目录结构）
                rel_path = os.path.relpath(root, SOURCE_DIR)
                target_subdir = TARGET_DIR / rel_path if rel_path != '.' else TARGET_DIR
                target_subdir.mkdir(parents=True, exist_ok=True)

                target_file = target_subdir / filename

                # 检查是否已存在
                if target_file.exists():
                    print(f"⏭️  跳过（已存在）: {filename}")
                    skip_count += 1
                    continue

                try:
                    # 复制文件
                    shutil.copy2(source_file, target_file)
                    success_count += 1
                    print(f"✅ 已复制: {filename}")
                except Exception as e:
                    print(f"❌ 复制失败 {filename}: {e}")

    print()
    print("=" * 60)
    print(f"📊 迁移完成统计:")
    print(f"   总文件数: {total_count}")
    print(f"   成功复制: {success_count}")
    print(f"   跳过文件: {skip_count}")
    print(f"   目标目录: {TARGET_DIR}")
    print("=" * 60)

    return True

if __name__ == "__main__":
    migrate_pdfs()
