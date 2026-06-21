"""
播客文案语音生成模块
基于 LongCat-AudioDiT 实现文本转语音（支持语音克隆）
"""

import os
import subprocess
import logging
from pathlib import Path
from typing import Optional, List
import numpy as np
import soundfile as sf

from podcast.text_preprocessor import preprocess_text, smart_split_text

logger = logging.getLogger(__name__)


class PodcastTTSGenerator:
    """播客TTS生成器"""
    
    def __init__(
        self,
        longcat_dir: str = "C:/LongCat/LongCat-AudioDiT",
        model_dir: str = "meituan-longcat/LongCat-AudioDiT-1B",
        output_dir: str = "./data/podcast_audio/"
    ):
        """
        初始化TTS生成器
        
        Args:
            longcat_dir: LongCat-AudioDiT 项目目录
            model_dir: 模型目录路径
            output_dir: 输出音频目录
        """
        self.longcat_dir = Path(longcat_dir)
        self.model_dir = model_dir
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 验证 LongCat 项目是否存在
        inference_script = self.longcat_dir / "inference.py"
        if not inference_script.exists():
            raise FileNotFoundError(
                f"LongCat-AudioDiT 推理脚本不存在: {inference_script}\n"
                f"请确认 longcat_dir 参数正确指向 C:/LongCat/LongCat-AudioDiT"
            )
    
    def generate_speech(
        self,
        text: str,
        ref_audio_path: str,
        prompt_text: str,
        output_filename: Optional[str] = None,
        nfe: int = 18,
        guidance_strength: float = 3.5,
        guidance_method: str = "apg",
        enable_split: bool = True,
        split_max_chars: int = 40,
        split_silence_ms: int = 200,
        seed: int = 1024,
    ) -> str:
        """
        生成语音（支持长文本自动分段）
        
        Args:
            text: 要转换的文本
            ref_audio_path: 参考音频路径（3-8秒）
            prompt_text: 参考音频对应的文本
            output_filename: 输出文件名（可选，默认自动生成）
            nfe: ODE步数（14-20）
            guidance_strength: 引导强度（3.2-3.8）
            guidance_method: 引导方式（cfg/apg）
            enable_split: 是否启用长文本分段
            split_max_chars: 每段最大字符数
            split_silence_ms: 段间停顿毫秒数
            seed: 随机种子
            
        Returns:
            生成的音频文件路径
        """
        try:
            # 1. 文本预处理
            logger.info("开始文本预处理...")
            processed_text = preprocess_text(text)
            
            # 2. 智能分句
            if enable_split:
                logger.info(f"智能分句（max_chars={split_max_chars}）...")
                segments = smart_split_text(processed_text, split_max_chars)
                logger.info(f"分为 {len(segments)} 段")
            else:
                segments = [processed_text]
            
            # 3. 生成输出文件名
            if not output_filename:
                import time
                timestamp = int(time.time() * 1000)
                output_filename = f"podcast_{timestamp}.wav"
            
            output_path = self.output_dir / output_filename
            
            # 4. 如果只有一段，直接调用
            if len(segments) == 1:
                logger.info("单段合成...")
                return self._synthesize_single_segment(
                    text=segments[0],
                    ref_audio_path=ref_audio_path,
                    prompt_text=prompt_text,
                    output_path=str(output_path),
                    nfe=nfe,
                    guidance_strength=guidance_strength,
                    guidance_method=guidance_method,
                    seed=seed,
                )
            
            # 5. 多段合成并拼接
            logger.info("多段合成...")
            segment_files = []
            
            for i, segment in enumerate(segments, 1):
                logger.info(f"合成第 {i}/{len(segments)} 段...")
                
                seg_output = self.output_dir / f"temp_seg_{i}_{int(time.time()*1000)}.wav"
                
                self._synthesize_single_segment(
                    text=segment,
                    ref_audio_path=ref_audio_path,
                    prompt_text=prompt_text,
                    output_path=str(seg_output),
                    nfe=nfe,
                    guidance_strength=guidance_strength,
                    guidance_method=guidance_method,
                    seed=seed + i,  # 每段使用不同的种子
                )
                
                segment_files.append(str(seg_output))
                
                # 添加段间停顿
                if i < len(segments) and split_silence_ms > 0:
                    silence_duration = split_silence_ms / 1000.0
                    silence_file = self._create_silence(silence_duration, sample_rate=24000)
                    segment_files.append(silence_file)
            
            # 6. 拼接所有音频段
            logger.info("拼接音频段...")
            self._concatenate_audio(segment_files, str(output_path))
            
            # 7. 清理临时文件
            logger.info("清理临时文件...")
            self._cleanup_temp_files(segment_files)
            
            logger.info(f"✅ 语音生成完成: {output_path}")
            return str(output_path)
            
        except Exception as e:
            logger.error(f"❌ 语音生成失败: {e}", exc_info=True)
            raise
    
    def _synthesize_single_segment(
        self,
        text: str,
        ref_audio_path: str,
        prompt_text: str,
        output_path: str,
        nfe: int = 18,
        guidance_strength: float = 3.5,
        guidance_method: str = "apg",
        seed: int = 1024,
    ) -> str:
        """
        合成单个音频段
        
        Args:
            text: 文本内容
            ref_audio_path: 参考音频路径
            prompt_text: 参考音频对应的文本
            output_path: 输出路径
            nfe: ODE步数
            guidance_strength: 引导强度
            guidance_method: 引导方式
            seed: 随机种子
            
        Returns:
            输出音频路径
        """
        inference_script = self.longcat_dir / "inference.py"
        
        cmd = [
            "python", str(inference_script),
            "--text", text,
            "--prompt_text", prompt_text,
            "--prompt_audio", ref_audio_path,
            "--output_audio", output_path,
            "--model_dir", self.model_dir,
            "--nfe", str(nfe),
            "--guidance_strength", str(guidance_strength),
            "--guidance_method", guidance_method,
            "--seed", str(seed),
        ]
        
        logger.debug(f"执行命令: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=300  # 5分钟超时
            )
            
            if result.returncode != 0:
                error_msg = result.stderr[-500:] if result.stderr else "未知错误"
                raise RuntimeError(f"LongCat 推理失败: {error_msg}")
            
            if not Path(output_path).exists():
                raise RuntimeError(f"输出文件未生成: {output_path}")
            
            logger.info(f"✓ 段合成完成: {Path(output_path).name}")
            return output_path
            
        except subprocess.TimeoutExpired:
            raise RuntimeError("TTS 推理超时（300秒）")
        except Exception as e:
            raise RuntimeError(f"TTS 推理失败: {e}")
    
    def _create_silence(self, duration: float, sample_rate: int = 24000) -> str:
        """
        创建静音音频段
        
        Args:
            duration: 时长（秒）
            sample_rate: 采样率
            
        Returns:
            静音音频文件路径
        """
        import time
        silence_file = self.output_dir / f"temp_silence_{int(time.time()*1000)}.wav"
        
        num_samples = int(duration * sample_rate)
        silence = np.zeros((num_samples,), dtype=np.float32)
        sf.write(str(silence_file), silence, sample_rate)
        
        return str(silence_file)
    
    def _concatenate_audio(self, audio_files: List[str], output_path: str):
        """
        拼接多个音频文件
        
        Args:
            audio_files: 音频文件路径列表
            output_path: 输出路径
        """
        if not audio_files:
            raise ValueError("音频文件列表为空")
        
        all_segments = []
        sample_rate = None
        
        for audio_file in audio_files:
            data, sr = sf.read(audio_file)
            if sample_rate is None:
                sample_rate = sr
            elif sample_rate != sr:
                raise ValueError(f"采样率不一致: {audio_file} 的采样率为 {sr}，期望 {sample_rate}")
            all_segments.append(data)
        
        # 拼接所有段
        concatenated = np.concatenate(all_segments)
        sf.write(output_path, concatenated, sample_rate)
    
    def _cleanup_temp_files(self, file_paths: List[str]):
        """清理临时文件"""
        for file_path in file_paths:
            try:
                path = Path(file_path)
                if path.exists() and path.name.startswith("temp_"):
                    path.unlink()
                    logger.debug(f"已删除临时文件: {path.name}")
            except Exception as e:
                logger.warning(f"删除临时文件失败 {file_path}: {e}")


# 全局实例（单例模式）
_tts_generator = None


def get_tts_generator(
    longcat_dir: str = "C:/LongCat/LongCat-AudioDiT",
    model_dir: str = "meituan-longcat/LongCat-AudioDiT-1B",
    output_dir: str = "./data/podcast_audio/"
) -> PodcastTTSGenerator:
    """获取TTS生成器实例（单例模式）"""
    global _tts_generator
    if _tts_generator is None:
        _tts_generator = PodcastTTSGenerator(
            longcat_dir=longcat_dir,
            model_dir=model_dir,
            output_dir=output_dir
        )
    return _tts_generator


def generate_podcast_audio(
    text: str,
    ref_audio_path: str,
    prompt_text: str,
    **kwargs
) -> str:
    """便捷函数：生成播客语音"""
    generator = get_tts_generator()
    return generator.generate_speech(
        text=text,
        ref_audio_path=ref_audio_path,
        prompt_text=prompt_text,
        **kwargs
    )
