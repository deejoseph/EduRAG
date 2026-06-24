"""
数据备份脚本
在导入完成后使用，将data目录备份到backup目录
"""

import shutil
from pathlib import Path
from datetime import datetime


def backup_data_dir():
    """备份data目录到backup目录"""
    
    # 源目录
    source = Path("data")
    
    if not source.exists():
        print(f"❌ 源目录不存在: {source}")
        return False
    
    # 备份目录
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_root = Path("backup")
    backup_root.mkdir(exist_ok=True)
    
    backup_dest = backup_root / f"data_backup_{timestamp}"
    
    print(f"📦 开始备份...")
    print(f"   源目录: {source.absolute()}")
    print(f"   目标目录: {backup_dest.absolute()}")
    
    try:
        # 复制整个data目录
        shutil.copytree(source, backup_dest, dirs_exist_ok=True)
        
        # 计算备份大小
        total_size = sum(f.stat().st_size for f in backup_dest.rglob('*') if f.is_file())
        size_mb = total_size / (1024 * 1024)
        
        print(f"\n✅ 备份完成！")
        print(f"   备份位置: {backup_dest}")
        print(f"   备份大小: {size_mb:.2f} MB")
        print(f"   包含文件: {len(list(backup_dest.rglob('*')))} 个")
        
        # 清理旧备份（保留最近3个）
        old_backups = sorted(backup_root.glob("data_backup_*"))
        if len(old_backups) > 3:
            for old in old_backups[:-3]:
                print(f"   删除旧备份: {old}")
                shutil.rmtree(old)
        
        return True
        
    except Exception as e:
        print(f"\n❌ 备份失败: {e}")
        return False


def backup_chroma_db_only():
    """只备份chroma_db向量数据库"""
    
    chroma_path = Path("data/chroma_db")
    
    if not chroma_path.exists():
        print(f"❌ ChromaDB目录不存在: {chroma_path}")
        return False
    
    # 备份目录
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_root = Path("backup")
    backup_root.mkdir(exist_ok=True)
    
    backup_dest = backup_root / f"chroma_db_{timestamp}"
    
    print(f"📦 开始备份ChromaDB...")
    print(f"   源目录: {chroma_path.absolute()}")
    print(f"   目标目录: {backup_dest.absolute()}")
    
    try:
        shutil.copytree(chroma_path, backup_dest, dirs_exist_ok=True)
        
        # 计算备份大小
        total_size = sum(f.stat().st_size for f in backup_dest.rglob('*') if f.is_file())
        size_mb = total_size / (1024 * 1024)
        
        print(f"\n✅ ChromaDB备份完成！")
        print(f"   备份位置: {backup_dest}")
        print(f"   备份大小: {size_mb:.2f} MB")
        
        # 清理旧备份（保留最近3个）
        old_backups = sorted(backup_root.glob("chroma_db_*"))
        if len(old_backups) > 3:
            for old in old_backups[:-3]:
                print(f"   删除旧备份: {old}")
                shutil.rmtree(old)
        
        return True
        
    except Exception as e:
        print(f"\n❌ 备份失败: {e}")
        return False


if __name__ == "__main__":
    import sys
    
    print("="*60)
    print("  EduRAG 数据备份工具")
    print("="*60)
    print()
    
    # 选择备份类型
    if len(sys.argv) > 1 and sys.argv[1] == "--chroma-only":
        success = backup_chroma_db_only()
    else:
        print("选择备份模式:")
        print("  1. 完整备份 (整个data目录)")
        print("  2. 仅备份ChromaDB")
        print("  提示: 使用 --chroma-only 参数可快速只备份向量数据库")
        print()
        
        choice = input("请选择 (1/2, 默认1): ").strip()
        
        if choice == "2":
            success = backup_chroma_db_only()
        else:
            success = backup_data_dir()
    
    print()
    if success:
        print("🎉 备份成功完成！")
    else:
        print("⚠️  备份失败，请检查错误信息")
