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
    def __init__(self, pages_repo_path=None):
        """
        初始化部署器
        
        参数：
        pages_repo_path: GitHub Pages仓库的路径（可选）
                        如果提供，将直接推送到该仓库
                        否则推送到当前仓库的podcast-output目录
        """
        self.project_root = project_root
        
        if pages_repo_path:
            # 使用外部GitHub Pages仓库
            self.pages_root = Path(pages_repo_path)
            if not self.pages_root.exists():
                raise FileNotFoundError(f"GitHub Pages仓库路径不存在: {pages_repo_path}")
            print(f"[OK] 使用外部GitHub Pages仓库: {self.pages_root}")
        else:
            # 使用当前仓库的podcast-output目录
            self.pages_root = project_root / "podcast-output"
            print("[INFO] 使用当前仓库的podcast-output目录")
        
        self.output_dir = self.pages_root
        self.audio_dir = self.output_dir / "audio"
        self.rss_file = self.output_dir / "feed.xml"
        
        # 确保输出目录存在
        self.output_dir.mkdir(exist_ok=True)
        self.audio_dir.mkdir(exist_ok=True)
        
        # 初始化数据库
        self.db = EduRAGDatabase()
        
    def get_completed_scripts(self, limit=50):
        """获取所有已完成的播客文案（从JSON状态管理器读取）"""
        if not self.db.collection_exists('podcast_scripts'):
            print("[WARN] 播客文案集合不存在")
            return []
        
        # 从JSON状态管理器获取所有completed状态的文案ID
        from podcast.script_state_manager import get_script_state_manager
        state_mgr = get_script_state_manager()
        all_states = state_mgr.get_all_states()
        completed_script_ids = [
            sid for sid, state in all_states.items() 
            if state.get('status') == 'completed'
        ]
        
        if not completed_script_ids:
            print("[WARN] 没有找到状态为completed的播客文案")
            return []
        
        collection = self.db.get_collection('podcast_scripts')
        
        # 构建查询条件
        if len(completed_script_ids) == 1:
            where_filter = {
                '$and': [
                    {'type': 'podcast_script'},
                    {'script_id': completed_script_ids[0]}
                ]
            }
        else:
            where_filter = {
                '$and': [
                    {'type': 'podcast_script'},
                    {'$or': [{'script_id': sid} for sid in completed_script_ids]}
                ]
            }
        
        results = collection.get(
            where=where_filter,
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
        
        print(f"[OK] 找到 {len(scripts)} 个已完成的播客文案")
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
            print(f"[SKIP] 音频文件已存在，跳过: {script_id}")
            return str(audio_path)
        
        # TODO: 这里应该调用真实的TTS API
        # 例如：Azure TTS, 阿里云TTS, 或本地的tts_generator
        print(f"[WARN] TTS音频生成功能待实现，创建占位符文件: {script_id}")
        
        # 创建占位符文件（仅用于测试）
        with open(audio_path, 'w', encoding='utf-8') as f:
            f.write(f"<!-- Placeholder for audio: {script_id} -->")
        
        return str(audio_path)
    
    def generate_rss_feed(self, scripts):
        """
        生成RSS Feed XML文件（支持4个独立阶段）
        
        为每个阶段生成独立的feed文件：
        - feed-shenti.xml (审题分析)
        - feed-gousi.xml (构思提纲)
        - feed-xiezuo.xml (写作辅助)
        - feed-pinggu.xml (写作评估)
        """
        print("[INFO] 生成RSS Feed...")
        
        # 按stage分组
        from podcast.script_state_manager import get_script_state_manager
        state_mgr = get_script_state_manager()
        all_states = state_mgr.get_all_states()
        
        stage_scripts = {
            'shenti': [],
            'gousi': [],
            'xiezuo': [],
            'pinggu': []
        }
        
        for script in scripts:
            metadata = script['metadata']
            content = script['content']
            script_id = metadata.get('script_id', '')
            
            # 获取stage
            stage = all_states.get(script_id, {}).get('stage')
            if not stage or stage not in stage_scripts:
                print(f"[WARN] 文案 {script_id} 未设置stage或stage无效，跳过")
                continue
            
            # 构建音频URL
            audio_url = f"https://dee422.github.io/audio/{script_id}.mp3"
            metadata_copy = metadata.copy()
            metadata_copy['audio_url'] = audio_url
            
            stage_scripts[stage].append((metadata_copy, content))
        
        # 为每个stage生成独立的feed文件
        stage_names = {
            'shenti': '审题分析',
            'gousi': '构思提纲',
            'xiezuo': '写作辅助',
            'pinggu': '写作评估'
        }
        
        generated_files = []
        for stage, stage_name in stage_names.items():
            if not stage_scripts[stage]:
                print(f"[WARN] 阶段 '{stage_name}' 没有completed文案，跳过")
                continue
            
            # 生成该阶段的RSS XML
            rss_xml = _generate_rss_xml(stage_scripts[stage])
            
            # 写入文件
            rss_file = self.output_dir / f"feed-{stage}.xml"
            with open(rss_file, 'w', encoding='utf-8') as f:
                f.write(rss_xml)
            
            print(f"[OK] {stage_name} RSS已生成: {rss_file}")
            generated_files.append(str(rss_file))
        
        print(f"[INFO] 共生成 {len(generated_files)} 个RSS Feed文件")
        return True
    
    def commit_and_push(self, pages_repo_path=None):
        """提交并推送到GitHub"""
        print("[INFO] 提交并推送到GitHub...")
        
        try:
            # 确定Git仓库路径
            if pages_repo_path:
                git_repo_path = Path(pages_repo_path)
                print(f"[OK] 推送到外部仓库: {git_repo_path}")
            else:
                git_repo_path = self.project_root
                print(f"[INFO] 推送到当前仓库")
            
            # 检查是否有更改
            result = subprocess.run(
                ['git', 'status', '--porcelain'],
                capture_output=True,
                text=True,
                cwd=git_repo_path
            )
            
            if not result.stdout.strip():
                print("[INFO] 没有需要提交的更改")
                return True
            
            # 添加文件
            subprocess.run(
                ['git', 'add', '.'],
                check=True,
                cwd=git_repo_path
            )
            
            # 提交
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            commit_msg = f"chore: 更新播客文件 - {timestamp}"
            subprocess.run(
                ['git', 'commit', '-m', commit_msg],
                check=True,
                cwd=git_repo_path
            )
            
            # 推送
            subprocess.run(
                ['git', 'push', 'origin', 'main'],
                check=True,
                cwd=git_repo_path
            )
            
            print("[OK] 成功推送到GitHub")
            print("[INFO] GitHub Pages将在1-2分钟内自动部署")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"[ERROR] Git操作失败: {e}")
            return False
    
    def deploy(self, skip_audio=False, pages_repo_path=None):
        """执行完整部署流程"""
        print("=" * 60)
        print("[START] 播客自动化部署开始")
        print("=" * 60)
        
        # 1. 获取已完成的文案
        scripts = self.get_completed_scripts()
        if not scripts:
            print("[ERROR] 没有找到可部署的播客文案")
            return False
        
        # 2. 生成音频文件（可选）
        if not skip_audio:
            print("\n[STEP 1/3] 生成TTS音频文件")
            for script in scripts:
                script_id = script['metadata'].get('script_id', '')
                content = script['content']
                self.generate_tts_audio(script_id, content)
        else:
            print("\n[SKIP] 跳过音频生成")
        
        # 3. 生成RSS Feed
        print("\n[STEP 2/3] 生成RSS Feed")
        self.generate_rss_feed(scripts)
        
        # 4. 提交并推送
        print("\n[STEP 3/3] 提交到GitHub")
        success = self.commit_and_push(pages_repo_path=pages_repo_path)
        
        if success:
            print("\n" + "=" * 60)
            print("[SUCCESS] 部署完成！")
            print("=" * 60)
            print(f"\n[RSS URL] https://dee422.github.io/feed.xml")
            print(f"[AUDIO DIR] https://dee422.github.io/audio/")
            print("\n[INFO] 提示:")
            print("   1. 等待1-2分钟让GitHub Pages部署完成")
            print("   2. 访问上述URL验证文件是否正确部署")
            print("   3. 在小宇宙等平台提交RSS URL: https://dee422.github.io/feed.xml")
        else:
            print("\n[FAILED] 部署失败")
        
        return success


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='播客自动化部署工具')
    parser.add_argument('--skip-audio', action='store_true', 
                       help='跳过音频生成（仅更新RSS）')
    parser.add_argument('--limit', type=int, default=50,
                       help='处理的文案数量限制（默认50）')
    parser.add_argument('--pages-repo', type=str, default=None,
                       help='GitHub Pages仓库的路径（可选，默认使用当前仓库的podcast-output目录）')
    
    args = parser.parse_args()
    
    deployer = PodcastDeployer(pages_repo_path=args.pages_repo)
    success = deployer.deploy(skip_audio=args.skip_audio, pages_repo_path=args.pages_repo)
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
