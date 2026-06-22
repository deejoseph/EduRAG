"""
EduRAG 播客文案状态管理器
使用JSON文件管理文案状态和音频关联，避免ChromaDB更新问题
"""

import json
import logging
from pathlib import Path
from typing import Dict, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)


class PodcastScriptStateManager:
    """播客文案状态管理器"""
    
    def __init__(self, storage_path: str = "./data/podcast_scripts_state.json"):
        self.storage_file = Path(storage_path)
        self.storage_file.parent.mkdir(parents=True, exist_ok=True)
        
        # 加载或初始化状态文件
        self.state_data = self._load_or_init()
    
    def _load_or_init(self) -> Dict:
        """加载状态文件或创建新的"""
        if self.storage_file.exists():
            try:
                with open(self.storage_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"加载状态文件失败，创建新文件: {e}")
                return {"scripts": {}}
        else:
            return {"scripts": {}}
    
    def _save(self):
        """保存状态到文件"""
        try:
            with open(self.storage_file, 'w', encoding='utf-8') as f:
                json.dump(self.state_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存状态文件失败: {e}")
    
    def update_script_status(self, script_id: str, status: str) -> bool:
        """
        更新文案状态
        
        Args:
            script_id: 文案ID
            status: 状态 (draft/completed/archived)
            
        Returns:
            bool: 是否成功
        """
        if script_id not in self.state_data["scripts"]:
            self.state_data["scripts"][script_id] = {}
        
        self.state_data["scripts"][script_id]["status"] = status
        self.state_data["scripts"][script_id]["updated_at"] = datetime.now().isoformat()
        self._save()
        
        logger.info(f"✅ 文案状态已更新: {script_id} -> {status}")
        return True
    
    def get_script_status(self, script_id: str) -> Optional[str]:
        """获取文案状态"""
        if script_id in self.state_data["scripts"]:
            return self.state_data["scripts"][script_id].get("status")
        return None
    
    def add_audio_association(self, script_id: str, audio_id: str) -> bool:
        """
        添加音频关联
        
        Args:
            script_id: 文案ID
            audio_id: 音频ID
            
        Returns:
            bool: 是否成功
        """
        if script_id not in self.state_data["scripts"]:
            self.state_data["scripts"][script_id] = {"audio_files": []}
        
        if "audio_files" not in self.state_data["scripts"][script_id]:
            self.state_data["scripts"][script_id]["audio_files"] = []
        
        if audio_id not in self.state_data["scripts"][script_id]["audio_files"]:
            self.state_data["scripts"][script_id]["audio_files"].append(audio_id)
            self.state_data["scripts"][script_id]["updated_at"] = datetime.now().isoformat()
            self._save()
            logger.info(f"✅ 音频关联已添加: {script_id} + {audio_id}")
            return True
        
        return False
    
    def remove_audio_association(self, script_id: str, audio_id: str) -> bool:
        """移除音频关联"""
        if script_id in self.state_data["scripts"]:
            if "audio_files" in self.state_data["scripts"][script_id]:
                if audio_id in self.state_data["scripts"][script_id]["audio_files"]:
                    self.state_data["scripts"][script_id]["audio_files"].remove(audio_id)
                    self.state_data["scripts"][script_id]["updated_at"] = datetime.now().isoformat()
                    self._save()
                    logger.info(f"✅ 音频关联已移除: {script_id} - {audio_id}")
                    return True
        return False
    
    def get_script_audio_files(self, script_id: str) -> List[str]:
        """获取文案关联的音频ID列表"""
        if script_id in self.state_data["scripts"]:
            return self.state_data["scripts"][script_id].get("audio_files", [])
        return []
    
    def get_all_states(self) -> Dict:
        """获取所有文案的状态"""
        return self.state_data["scripts"]


# 全局单例
_state_manager = None

def get_script_state_manager() -> PodcastScriptStateManager:
    """获取状态管理器单例"""
    global _state_manager
    if _state_manager is None:
        _state_manager = PodcastScriptStateManager()
    return _state_manager
