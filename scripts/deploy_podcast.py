#!/usr/bin/env python3
"""
播客自动化部署脚本
功能：
1. 从数据库获取已完成的播客文案
2. 生成TTS音频文件（可选）
3. 生成RSS Feed XML文件
4. 提交到Git并推送到GitHub Pages
"""

import os
import sys
import json
import hashlib
import subprocess
from datetime import datetime
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from api.routes.writing import _generate_rss_xml
from core.db_manager import EduRAGDatabase


class PodcastDeployer:
    def __init__(self):
        self.output_dir = project_root / "podcast-output"
        self.audio_dir = self.output_dir / "audio"
        self.rss_file = self.output_dir / "feed.xml"
        
        # 确保输出目录存在
        self.output_dir.mkdir(exist_ok=True)
        self.audio_dir.mkdir(exist_ok=True)
        
        # 初始化数据库
        self.db = EduRAGDatabase()
        
    def get_completed_scripts(self, limit=50):
        """获取所有已完成的播客文案"""
        if not self.db.collection_exists('podcast_scripts'):
            print("⚠️ 播客文案集合不存在")
            return []
        
        collection = self.db.get_collection('podcast_scripts')
        results = collection.get(
            where={'type': 'podcast_script', 'status': 'completed'},
            limit=limit,
            include=['metadatas', 'documents']
        )
        
        scripts = []
        for metadata, document in zip(results['metadatas'], results['documents']):
            scripts.append({
                'metadata': metadata,
                'content': document
            })
        
        # 按时间排序（最新的在前）
        scripts.sort(key=lambda x: x['metadata'].get('created_at', ''), reverse=True)
        
        print(f"✅ 找到 {len(scripts)} 个已完成的播客文案")
        return scripts
    
    def generate_tts_audio(self, script_id, content):
        """
        生成TTS音频文件
        TODO: 集成真实的TTS服务
        目前创建占位符文件
        """
        audio_path = self.audio_dir / f"{script_id}.mp3"
        
        # 如果音频文件已存在，跳过
        if audio_path.exists():
            print(f"⏭️ 音频文件已存在，跳过: {script_id}")
            return str(audio_path)
        
        # TODO: 这里应该调用真实的TTS API
        # 例如：Azure TTS, 阿里云TTS, 或本地的tts_generator
        print(f"⚠️ TTS音频生成功能待实现，创建占位符文件: {script_id}")
        
        # 创建占位符文件（仅用于测试）
        with open(audio_path, 'w', encoding='utf-8') as f:
            f.write(f"<!-- Placeholder for audio: {script_id} -->")
        
        return str(audio_path)
    
    def generate_rss_feed(self, scripts):
        """生成RSS Feed XML文件"""
        print("📝 生成RSS Feed...")
        
        # 准备数据格式
        script_list = []
        for script in scripts:
            metadata = script['metadata']
            content = script['content']
            
            # 构建音频URL（GitHub Pages URL）
            script_id = metadata.get('script_id', '')
            audio_url = f"https://deejoseph.github.io/EduRAG/audio/{script_id}.mp3"
            
            # 替换metadata中的音频URL
            metadata_copy = metadata.copy()
            metadata_copy['audio_url'] = audio_url
            
            script_list.append((metadata_copy, content))
        
        # 生成RSS XML
        rss_xml = _generate_rss_xml(script_list)
        
        # 写入文件
        with open(self.rss_file, 'w', encoding='utf-8') as f:
            f.write(rss_xml)
        
        print(f"✅ RSS Feed已生成: {self.rss_file}")
        return True
    
    def commit_and_push(self):
        """提交并推送到GitHub"""
        print("🚀 提交并推送到GitHub...")
        
        try:
            # 检查是否有更改
            result = subprocess.run(
                ['git', 'status', '--porcelain', 'podcast-output/'],
                capture_output=True,
                text=True,
                cwd=project_root
            )
            
            if not result.stdout.strip():
                print("ℹ️ 没有需要提交的更改")
                return True
            
            # 添加文件
            subprocess.run(
                ['git', 'add', 'podcast-output/'],
                check=True,
                cwd=project_root
            )
            
            # 提交
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            commit_msg = f"chore: 更新播客文件 - {timestamp}"
            subprocess.run(
                ['git', 'commit', '-m', commit_msg],
                check=True,
                cwd=project_root
            )
            
            # 推送
            subprocess.run(
                ['git', 'push', 'origin', 'main'],
                check=True,
                cwd=project_root
            )
            
            print("✅ 成功推送到GitHub")
            print("📡 GitHub Pages将在1-2分钟内自动部署")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Git操作失败: {e}")
            return False
    
    def deploy(self, skip_audio=False):
        """执行完整部署流程"""
        print("=" * 60)
        print("🎙️ 播客自动化部署开始")
        print("=" * 60)
        
        # 1. 获取已完成的文案
        scripts = self.get_completed_scripts()
        if not scripts:
            print("❌ 没有找到可部署的播客文案")
            return False
        
        # 2. 生成音频文件（可选）
        if not skip_audio:
            print("\n🎵 步骤1: 生成TTS音频文件")
            for script in scripts:
                script_id = script['metadata'].get('script_id', '')
                content = script['content']
                self.generate_tts_audio(script_id, content)
        else:
            print("\n⏭️ 跳过音频生成")
        
        # 3. 生成RSS Feed
        print("\n📄 步骤2: 生成RSS Feed")
        self.generate_rss_feed(scripts)
        
        # 4. 提交并推送
        print("\n📤 步骤3: 提交到GitHub")
        success = self.commit_and_push()
        
        if success:
            print("\n" + "=" * 60)
            print("✅ 部署完成！")
            print("=" * 60)
            print(f"\n📡 RSS Feed URL: https://deejoseph.github.io/EduRAG/feed.xml")
            print(f"🎧 音频文件目录: https://deejoseph.github.io/EduRAG/audio/")
            print("\n💡 提示:")
            print("   1. 等待1-2分钟让GitHub Pages部署完成")
            print("   2. 访问上述URL验证文件是否正确部署")
            print("   3. 在小宇宙等平台提交RSS URL: https://deejoseph.github.io/EduRAG/feed.xml")
        else:
            print("\n❌ 部署失败")
        
        return success


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='播客自动化部署工具')
    parser.add_argument('--skip-audio', action='store_true', 
                       help='跳过音频生成（仅更新RSS）')
    parser.add_argument('--limit', type=int, default=50,
                       help='处理的文案数量限制（默认50）')
    
    args = parser.parse_args()
    
    deployer = PodcastDeployer()
    success = deployer.deploy(skip_audio=args.skip_audio)
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
