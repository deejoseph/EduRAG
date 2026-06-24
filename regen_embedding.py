#!/usr/bin/env python3
"""
重新生成所有数据的 embedding
1. 备份现有数据
2. 删除集合
3. 重新导入所有文档
"""
import sys
import os
sys.path.insert(0, '.')

from core.db_manager import EduRAGDatabase
import shutil
from datetime import datetime

def main():
    print("=" * 60)
    print("  EduRAG - 重新生成 Embedding")
    print("=" * 60)
    
    # 1. 检查当前状态
    db = EduRAGDatabase('./data/chroma_db')
    
    if not db.collection_exists('chinese_essays'):
        print("\n❌ 错误: chinese_essays 集合不存在")
        return
    
    coll = db.get_collection('chinese_essays')
    current_count = coll.count()
    print(f"\n📊 当前知识库状态:")
    print(f"   - 集合名称: chinese_essays")
    print(f"   - 文档数量: {current_count:,} 条")
    print(f"   - Embedding 模型: BAAI/bge-base-zh-v1.5 (768维)")
    
    # 2. 确认操作
    print("\n⚠️  警告: 此操作将删除现有集合并重新导入所有数据")
    print("   这可能需要 1-2 小时，请确保:")
    print("   1. 有足够的磁盘空间")
    print("   2. 不要中断进程")
    print("   3. 已完成数据备份")
    
    confirm = input("\n是否继续? (输入 'yes' 确认): ")
    if confirm.lower() != 'yes':
        print("\n❌ 操作已取消")
        return
    
    # 3. 创建备份
    print("\n📦 正在创建备份...")
    backup_root = './backup'
    os.makedirs(backup_root, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"chroma_db_before_regen_{timestamp}"
    backup_dest = os.path.join(backup_root, backup_name)
    
    try:
        shutil.copytree('./data/chroma_db', backup_dest)
        print(f"✅ 备份完成: {backup_dest}")
    except Exception as e:
        print(f"❌ 备份失败: {e}")
        return
    
    # 4. 删除集合
    print("\n🗑️  正在删除集合...")
    try:
        db.client.delete_collection('chinese_essays')
        print("✅ 集合已删除")
    except Exception as e:
        print(f"❌ 删除失败: {e}")
        return
    
    # 5. 重新导入
    print("\n🔄 开始重新导入数据...")
    print("   这将运行 import_docs.py 脚本")
    print("   预计耗时: 1-2 小时\n")
    
    import subprocess
    result = subprocess.run([
        sys.executable, 
        'scripts/import_docs.py',
        '--source', 'data/docs/all/',
        '--collection', 'chinese_essays'
    ], cwd='.')
    
    if result.returncode == 0:
        print("\n✅ 重新导入完成!")
        
        # 验证结果
        if db.collection_exists('chinese_essays'):
            new_coll = db.get_collection('chinese_essays')
            new_count = new_coll.count()
            print(f"\n📊 新的知识库状态:")
            print(f"   - 文档数量: {new_count:,} 条")
            print(f"   - Embedding 维度: 768维 (BAAI/bge-base-zh-v1.5)")
            
            if new_count > 0:
                print(f"\n✨ 成功! 共处理 {new_count:,} 条文档")
            else:
                print(f"\n⚠️  警告: 导入后文档数为 0，请检查日志")
    else:
        print(f"\n❌ 导入失败，退出码: {result.returncode}")
        print(f"   可以从备份恢复: {backup_dest}")

if __name__ == '__main__':
    main()
