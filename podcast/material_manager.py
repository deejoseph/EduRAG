"""
EduRAG 播客素材管理模块
负责从引导写作各阶段收集、存储和管理播客素材
"""

import os
import json
import logging
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class PodcastMaterialManager:
    """播客素材管理器"""
    
    def __init__(self, storage_path: str = "./data/podcast_materials/"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
    def add_stage_material(
        self,
        stage: str,
        topic: str,
        content: str,
        ai_model: str = "default",
        metadata: Optional[Dict] = None
    ) -> str:
        """
        添加单个阶段的播客素材
        
        Args:
            stage: 阶段名称 (analysis/outline/essay/evaluation)
            topic: 作文题目
            content: AI生成的内容
            ai_model: 使用的AI模型名称
            metadata: 额外元数据
            
        Returns:
            material_id: 素材ID
        """
        material_id = f"POD_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{stage}"
        
        material_data = {
            "id": material_id,
            "stage": stage,
            "topic": topic,
            "content": content,
            "ai_model": ai_model,
            "metadata": metadata or {},
            "created_at": datetime.now().isoformat(),
            "status": "pending"  # pending | selected | imported
        }
        
        # 保存为JSON文件
        file_path = self.storage_path / f"{material_id}.json"
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(material_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"✅ 播客素材已保存: {material_id}")
        return material_id
    
    def get_material(self, material_id: str) -> Optional[Dict]:
        """获取单个素材"""
        file_path = self.storage_path / f"{material_id}.json"
        if not file_path.exists():
            return None
        
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def list_materials(
        self,
        topic: Optional[str] = None,
        stage: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[Dict]:
        """
        列出素材
        
        Args:
            topic: 按题目过滤
            stage: 按阶段过滤
            status: 按状态过滤
            
        Returns:
            素材列表（按时间倒序）
        """
        materials = []
        
        for file_path in self.storage_path.glob("*.json"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # 应用过滤条件
                if topic and data.get('topic') != topic:
                    continue
                if stage and data.get('stage') != stage:
                    continue
                if status and data.get('status') != status:
                    continue
                
                materials.append(data)
            except Exception as e:
                logger.warning(f"读取素材文件失败 {file_path}: {e}")
        
        # 按创建时间倒序排序
        materials.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        return materials
    
    def update_status(self, material_id: str, status: str) -> bool:
        """更新素材状态"""
        material = self.get_material(material_id)
        if not material:
            return False
        
        material['status'] = status
        material['updated_at'] = datetime.now().isoformat()
        
        file_path = self.storage_path / f"{material_id}.json"
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(material, f, ensure_ascii=False, indent=2)
        
        return True
    
    # 别名方法，保持API一致性
    update_material_status = update_status
    
    def create_podcast_episode(
        self,
        topic: str,
        analysis_id: str,
        outline_id: str,
        essay_id: str,
        evaluation_id: str
    ) -> str:
        """
        创建完整的播客剧集（整合四个阶段的素材）
        
        Args:
            topic: 作文题目
            analysis_id: 审题素材ID
            outline_id: 构思素材ID
            essay_id: 范文素材ID
            evaluation_id: 评估素材ID
            
        Returns:
            episode_id: 剧集ID
        """
        # 加载各个阶段的素材
        analysis = self.get_material(analysis_id)
        outline = self.get_material(outline_id)
        essay = self.get_material(essay_id)
        evaluation = self.get_material(evaluation_id)
        
        if not all([analysis, outline, essay, evaluation]):
            raise ValueError("部分素材不存在")
        
        # 生成剧集ID
        episode_id = f"EPISODE_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # 整合为播客剧集
        episode_data = {
            "id": episode_id,
            "type": "podcast_episode",
            "topic": topic,
            "stages": {
                "analysis": {
                    "material_id": analysis_id,
                    "content": analysis['content'],
                    "ai_model": analysis.get('ai_model', 'unknown')
                },
                "outline": {
                    "material_id": outline_id,
                    "content": outline['content'],
                    "ai_model": outline.get('ai_model', 'unknown')
                },
                "essay": {
                    "material_id": essay_id,
                    "content": essay['content'],
                    "ai_model": essay.get('ai_model', 'unknown')
                },
                "evaluation": {
                    "material_id": evaluation_id,
                    "content": evaluation['content'],
                    "ai_model": evaluation.get('ai_model', 'unknown')
                }
            },
            "created_at": datetime.now().isoformat(),
            "status": "ready_for_script"  # ready_for_script | script_generated | audio_generated | published
        }
        
        # 保存剧集
        file_path = self.storage_path / f"{episode_id}.json"
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(episode_data, f, ensure_ascii=False, indent=2)
        
        # 更新各个素材的状态为已导入
        for mid in [analysis_id, outline_id, essay_id, evaluation_id]:
            self.update_status(mid, "imported")
        
        logger.info(f"✅ 播客剧集已创建: {episode_id}")
        return episode_id
    
    def delete_material(self, material_id: str) -> bool:
        """删除素材"""
        file_path = self.storage_path / f"{material_id}.json"
        if file_path.exists():
            file_path.unlink()
            logger.info(f"🗑️ 素材已删除: {material_id}")
            return True
        return False


# 全局实例（单例模式）
_podcast_manager = None


def get_podcast_manager() -> PodcastMaterialManager:
    """获取播客素材管理器实例"""
    global _podcast_manager
    if _podcast_manager is None:
        _podcast_manager = PodcastMaterialManager()
    return _podcast_manager

