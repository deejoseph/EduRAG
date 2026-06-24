/**
 * 播客模块主页面
 * 展示从写作训练各阶段导入的素材，支持查看、编辑和管理
 */

import React, { useState, useEffect } from 'react';
import { Card, Table, Tag, Button, Space, Typography, Empty, Modal, message, Badge, Input, Select, Upload, Progress, Divider, Tabs, List, Alert } from 'antd';
import { SoundOutlined, EyeOutlined, DeleteOutlined, DownloadOutlined, StarOutlined, PlayCircleOutlined, PauseCircleOutlined, CloudUploadOutlined, CopyOutlined, EditOutlined, SaveOutlined, DatabaseOutlined, StopOutlined } from '@ant-design/icons';
import { writingApi } from '../../api/writing';
import type { PodcastMaterial, PodcastScript } from '../../api/writing';

const { Title, Text, Paragraph } = Typography;
const { TextArea } = Input;
const { Option } = Select;

const PodcastPage: React.FC = () => {
  const [materials, setMaterials] = useState<PodcastMaterial[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedMaterial, setSelectedMaterial] = useState<PodcastMaterial | null>(null);
  const [viewModalVisible, setViewModalVisible] = useState(false);
  
  // 多选相关状态
  const [selectedRowKeys, setSelectedRowKeys] = useState<string[]>([]);
  const [generateModalVisible, setGenerateModalVisible] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [generatedScript, setGeneratedScript] = useState<string>('');
  const [prompt, setPrompt] = useState('请将这些素材整理成一段单人播客文案，风格轻松有趣。重要要求：1.不要出现任何括号内容如（笑声）、（掌声）等环境交代；2.不要出现【播客文案】、场景描述、氛围渲染、情绪标注、角色标记等多余内容；3.只保留纯对话文本，直接输出内容即可。');
  const [selectedModel, setSelectedModel] = useState('qwen3:8b');
  
  // TTS语音生成相关状态
  const [ttsModalVisible, setTtsModalVisible] = useState(false);
  const [ttsGenerating, setTtsGenerating] = useState(false);
  const [refAudioFile, setRefAudioFile] = useState<File | null>(null);
  const [savedRefAudioId, setSavedRefAudioId] = useState<string | null>(null); // 已保存的参考音频ID
  const [refAudios, setRefAudios] = useState<Array<{id: string; name: string; prompt_text?: string}>>([]); // 已保存的音频列表
  const [loadingRefAudios, setLoadingRefAudios] = useState(false);
  const [promptText, setPromptText] = useState('这是一段播客对话');
  const [ttsMode, setTtsMode] = useState<'precise' | 'standard' | 'fast'>('standard');
  const [nfe, setNfe] = useState(22); // 增加NFE提高音质，减少破音
  const [guidanceStrength, setGuidanceStrength] = useState(2.8); // 降低引导强度，避免失真
  const [audioSegments, setAudioSegments] = useState<Array<{text: string; audio_url?: string; duration?: number; status: 'pending' | 'generating' | 'completed' | 'failed'}>>([]);
  const [savedAudioSegments, setSavedAudioSegments] = useState<Array<{text: string; audio_url?: string; duration?: number; status: 'pending' | 'generating' | 'completed' | 'failed'}>>([]); // 保存的分段数据，关闭弹窗后保留
  const [fullAudioUrl, setFullAudioUrl] = useState<string | null>(null); // 完整合并音频的URL
  const [currentPlayingIndex, setCurrentPlayingIndex] = useState<number | null>(null);
  const [audioPlayer, setAudioPlayer] = useState<HTMLAudioElement | null>(null);
  
  // TTS生成中止控制
  const [ttsAbortController, setTtsAbortController] = useState<AbortController | null>(null);
  
  // 中止TTS生成
  const handleAbortTTS = () => {
    if (ttsAbortController) {
      ttsAbortController.abort();
      setTtsAbortController(null);
      setTtsGenerating(false);
      message.info('已中止语音生成');
    }
  };
  
  // 文案列表管理（从数据库加载）
  const [activeTab, setActiveTab] = useState<'materials' | 'scripts'>('materials');
  const [scriptList, setScriptList] = useState<PodcastScript[]>([]);
  const [loadingScripts, setLoadingScripts] = useState(false);
  const [currentScriptId, setCurrentScriptId] = useState<string | null>(null); // 当前正在编辑的文案ID
  
  // 文案列表筛选和分页
  const [scriptPage, setScriptPage] = useState(1);
  const [scriptPageSize, setScriptPageSize] = useState(10);
  const [stageFilter, setStageFilter] = useState<string | undefined>(undefined);
  const [statusFilter, setStatusFilter] = useState<string | undefined>(undefined);
  
  // 文案列表选择和批量操作
  const [selectedScriptIds, setSelectedScriptIds] = useState<string[]>([]);
  
  // 阶段编辑弹窗
  const [stageModalVisible, setStageModalVisible] = useState(false);
  const [currentEditScriptId, setCurrentEditScriptId] = useState<string | null>(null);
  const [selectedStage, setSelectedStage] = useState<string | undefined>(undefined);
  
  // 音频关联弹窗
  const [audioModalVisible, setAudioModalVisible] = useState(false);
  const [selectedAudioIds, setSelectedAudioIds] = useState<string[]>([]);
  const [audioFileList, setAudioFileList] = useState<Array<{ filename: string; size_mb: number; created_at: string }>>([]);
  
  // RSS相关状态
  const [rssModalVisible, setRssModalVisible] = useState(false);
  const [generatingRSS, setGeneratingRSS] = useState(false);
  const [rssXmlContent, setRssXmlContent] = useState<string>('');
  const [rssDownloadUrl, setRssDownloadUrl] = useState<string>('');
  
  // 从 localStorage 恢复文案和分段数据（页面刷新后保留）
  useEffect(() => {
    try {
      const savedScript = localStorage.getItem('podcast_generated_script');
      const savedSegments = localStorage.getItem('podcast_saved_segments');
      const savedFullUrl = localStorage.getItem('podcast_full_audio_url');
      const savedRefAudioId = localStorage.getItem('podcast_ref_audio_id'); // 恢复参考音频ID
      
      if (savedScript) {
        console.log('[Podcast] 从 localStorage 恢复文案:', savedScript.length, '字符');
        setGeneratedScript(savedScript);
      }
      
      if (savedRefAudioId) {
        console.log('[Podcast] 从 localStorage 恢复参考音频ID:', savedRefAudioId);
        setSavedRefAudioId(savedRefAudioId);
      }
      
      if (savedSegments) {
        console.log('[Podcast] 从 localStorage 恢复分段数据');
        setSavedAudioSegments(JSON.parse(savedSegments));
      }
      
      if (savedFullUrl) {
        console.log('[Podcast] 从 localStorage 恢复完整音频URL');
        setFullAudioUrl(savedFullUrl);
      }
    } catch (error) {
      console.error('[Podcast] 恢复本地数据失败:', error);
    }
  }, []);

  // 当筛选条件变化时，重新加载文案列表
  useEffect(() => {
    loadScripts();
  }, [stageFilter, statusFilter]);

  // 加载素材列表
  const loadMaterials = async () => {
    setLoading(true);
    try {
      const response = await writingApi.getPodcastMaterials();
      setMaterials(response.materials || []);
    } catch (error) {
      console.error('加载素材失败:', error);
      message.error('加载素材失败');
    } finally {
      setLoading(false);
    }
  };

  // 加载文案列表（从数据库）
  const loadScripts = async () => {
    setLoadingScripts(true);
    try {
      const params: any = { limit: 100 }; // 获取较多数据用于前端分页
      if (stageFilter) params.stage = stageFilter;
      if (statusFilter) params.status = statusFilter;
      
      const response = await writingApi.getPodcastScripts(params);
      setScriptList(response.scripts || []);
      console.log('[Podcast] 加载文案列表:', response.count, '个');
      
      // 【调试】打印前3个文案的元数据，检查字段是否正确
      if (response.scripts && response.scripts.length > 0) {
        console.log('[Podcast] ========== 文案列表元数据示例 ==========');
        response.scripts.slice(0, 3).forEach((script: any, index: number) => {
          console.log(`[Podcast] 文案 ${index + 1}:`, {
            script_id: script.script_id,
            title: script.title,
            topic: script.topic,
            essay_type: script.essay_type,
            grade_level: script.grade_level,
            essay_style: script.essay_style,
            word_count: script.word_count,
            source: script.source,
            score: script.score,
            stage: script.stage,
            question_type: script.question_type,
            question_name: script.question_name,
          });
        });
        console.log('[Podcast] ======================================');
      }
    } catch (error) {
      console.error('加载文案列表失败:', error);
      message.error('加载文案列表失败');
    } finally {
      setLoadingScripts(false);
    }
  };

  // 加载参考音频列表
  const loadRefAudios = async () => {
    setLoadingRefAudios(true);
    try {
      const response = await writingApi.getRefAudios();
      setRefAudios(response.audios || []);
      console.log('[Podcast] 加载参考音频列表:', response.audios?.length || 0, '个');
      
      // 如果 localStorage 中有 savedRefAudioId，尝试恢复对应的 prompt_text
      const savedRefAudioId = localStorage.getItem('podcast_ref_audio_id');
      if (savedRefAudioId && response.audios) {
        const selectedAudio = response.audios.find(a => a.id === savedRefAudioId);
        if (selectedAudio && selectedAudio.prompt_text) {
          console.log('[Podcast] 从已保存的音频中恢复 prompt_text:', selectedAudio.prompt_text);
          setPromptText(selectedAudio.prompt_text);
        }
      }
    } catch (error) {
      console.error('加载参考音频列表失败:', error);
    } finally {
      setLoadingRefAudios(false);
    }
  };

  // 打开已有文案进行编辑
  const handleOpenScript = async (script: PodcastScript) => {
    try {
      console.log('[Podcast] 打开文案:', script.script_id);
      const response = await writingApi.getPodcastScript(script.script_id);
      
      setGeneratedScript(response.script.content || '');
      setCurrentScriptId(script.script_id);
      
      // 清除旧的TTS分段数据
      setSavedAudioSegments([]);
      setAudioSegments([]);
      setFullAudioUrl(null);
      localStorage.removeItem('podcast_saved_segments');
      localStorage.removeItem('podcast_full_audio_url');
      
      message.success(`已加载文案：${script.title}`);
      
      // 自动打开生成文案Modal
      setGenerateModalVisible(true);
    } catch (error) {
      console.error('加载文案失败:', error);
      message.error('加载文案失败');
    }
  };

  // 复制文案（二次创作）
  const handleDuplicateScript = async (script: PodcastScript) => {
    try {
      console.log('[Podcast] 复制文案:', script.script_id);
      const response = await writingApi.duplicatePodcastScript(script.script_id);
      
      message.success(`文案已复制为新版本：${response.title}`);
      
      // 刷新列表
      loadScripts();
      
      // 自动打开新副本
      handleOpenScript({
        ...script,
        script_id: response.new_script_id,
        version: response.version,
        title: response.title
      });
    } catch (error) {
      console.error('复制文案失败:', error);
      message.error('复制文案失败');
    }
  };

  // 删除文案
  const handleDeleteScript = async (scriptId: string) => {
    Modal.confirm({
      title: '确认删除文案？',
      content: '删除后无法恢复，确定要删除吗？',
      okText: '确认删除',
      cancelText: '取消',
      okType: 'danger',
      onOk: async () => {
        try {
          await writingApi.deletePodcastScript(scriptId);
          message.success('文案已删除');
          loadScripts(); // 刷新列表
          
          // 如果删除的是当前正在编辑的文案，清空状态
          if (currentScriptId === scriptId) {
            setGeneratedScript('');
            setCurrentScriptId(null);
            setSavedAudioSegments([]);
            setAudioSegments([]);
            setFullAudioUrl(null);
            localStorage.removeItem('podcast_generated_script');
            localStorage.removeItem('podcast_saved_segments');
            localStorage.removeItem('podcast_full_audio_url');
          }
        } catch (error) {
          console.error('删除文案失败:', error);
          message.error('删除文案失败');
        }
      }
    });
  };

  // 更新文案状态
  const handleUpdateScriptStatus = async (scriptId: string, newStatus: 'draft' | 'completed' | 'archived') => {
    try {
      await writingApi.updatePodcastScriptStatus(scriptId, newStatus);
      message.success(`文案已标记为${newStatus === 'completed' ? '完成' : newStatus === 'draft' ? '草稿' : '归档'}`);
      loadScripts(); // 刷新列表
    } catch (error) {
      console.error('更新文案状态失败:', error);
      message.error('更新状态失败');
    }
  };

  // 打开阶段编辑弹窗
  const handleOpenStageModal = (scriptId: string, currentStage?: string) => {
    setCurrentEditScriptId(scriptId);
    setSelectedStage(currentStage);
    setStageModalVisible(true);
  };

  // 保存阶段设置
  const handleSaveStage = async () => {
    if (!currentEditScriptId || !selectedStage) {
      message.warning('请选择一个阶段');
      return;
    }
    
    try {
      await writingApi.updatePodcastScriptStage(currentEditScriptId, selectedStage as any);
      message.success('阶段设置成功');
      setStageModalVisible(false);
      loadScripts(); // 刷新列表
    } catch (error) {
      console.error('更新阶段失败:', error);
      message.error('更新阶段失败');
    }
  };

  // 打开音频关联弹窗
  const handleOpenAudioModal = async (scriptId: string) => {
    setCurrentEditScriptId(scriptId);
    setSelectedAudioIds([]);
    setAudioModalVisible(true);
    
    // 加载音频文件列表
    try {
      const response = await writingApi.listPodcastAudioFiles();
      setAudioFileList(response.files || []);
    } catch (error) {
      console.error('加载音频文件失败:', error);
      message.error('加载音频文件失败');
    }
  };

  // 保存音频关联
  const handleSaveAudioAssociation = async () => {
    if (!currentEditScriptId) return;
    
    try {
      for (const audioId of selectedAudioIds) {
        await writingApi.addAudioAssociation(currentEditScriptId, {
          audio_id: audioId,
        });
      }
      message.success('音频关联成功');
      setAudioModalVisible(false);
      loadScripts(); // 刷新列表
    } catch (error) {
      console.error('关联音频失败:', error);
      message.error('关联音频失败');
    }
  };

  // 添加文案到RAG知识库
  const handleAddScriptToRag = async (scriptId: string) => {
    Modal.confirm({
      title: '确认加入播客 RAG 知识库？',
      content: '将该播客文案存入播客 RAG 知识库，用于后续生成播客文案时学习历史风格',
      okText: '确认加入',
      cancelText: '取消',
      onOk: async () => {
        try {
          const response = await writingApi.addPodcastMaterialToRag(scriptId, {
            title: `播客文案_${scriptId}`
          });
          
          if (response.success) {
            message.success(`✅ 已存入播客 RAG 知识库，共 ${response.chunk_count} 个片段`);
            loadScripts();
          }
        } catch (error) {
          console.error('加入RAG失败:', error);
          message.error('加入RAG失败');
        }
      }
    });
  };

  useEffect(() => {
    loadMaterials();
    loadScripts(); // 加载文案列表
    loadRefAudios(); // 加载参考音频列表
    
    // 检查是否有未删除的文案（localStorage），如果有则自动打开TTS弹窗
    const checkSavedScript = () => {
      try {
        const savedScript = localStorage.getItem('podcast_generated_script');
        if (savedScript && savedScript.length > 0) {
          console.log('[Podcast] 检测到未删除的文案（localStorage），长度:', savedScript.length, '字符');
          console.log('[Podcast] 自动打开TTS弹窗，继续转语音进度');
          
          // 延迟打开，确保页面已加载
          setTimeout(() => {
            setGeneratedScript(savedScript);
            
            // 恢复分段数据
            const savedSegments = localStorage.getItem('podcast_saved_segments');
            if (savedSegments) {
              setSavedAudioSegments(JSON.parse(savedSegments));
              setAudioSegments(JSON.parse(savedSegments));
            }
            
            // 恢复完整音频URL
            const savedFullUrl = localStorage.getItem('podcast_full_audio_url');
            if (savedFullUrl) {
              setFullAudioUrl(savedFullUrl);
            }
            
            // 打开TTS弹窗
            setTtsModalVisible(true);
            message.info('检测到未完成的转语音任务，已自动恢复');
          }, 500);
        }
      } catch (error) {
        console.error('[Podcast] 检查本地数据失败:', error);
      }
    };
    
    checkSavedScript();
  }, []);

  // 删除素材
  const handleDelete = async (materialId: string) => {
    Modal.confirm({
      title: '确认删除',
      content: '确定要删除这个素材吗？此操作不可恢复。',
      okText: '删除',
      okType: 'danger',
      cancelText: '取消',
      onOk: async () => {
        try {
          await writingApi.deletePodcastMaterial(materialId);
          message.success('已删除');
          loadMaterials();
        } catch (error) {
          console.error('删除失败:', error);
          message.error('删除失败');
        }
      },
    });
  };

  // 查看素材详情
  const handleView = (material: PodcastMaterial) => {
    setSelectedMaterial(material);
    setViewModalVisible(true);
  };

  // 导出为文本文件
  const handleExport = (material: PodcastMaterial) => {
    const blob = new Blob([material.content], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `podcast_${material.stage}_${material.id}.txt`;
    link.click();
    URL.revokeObjectURL(url);
    message.success('已导出');
  };

  // 将素材存入RAG知识库
  const handleAddToRag = async (material: PodcastMaterial) => {
    Modal.confirm({
      title: '存入RAG知识库',
      content: `确定要将此素材存入RAG知识库吗？\n\n题目：${material.topic}\n阶段：${material.stage}`,
      okText: '确认存入',
      cancelText: '取消',
      onOk: async () => {
        try {
          const response = await writingApi.addPodcastMaterialToRag(material.id, {
            title: `播客素材_${material.topic}`
          });
          
          if (response.success) {
            message.success(`✅ 已存入RAG知识库，共 ${response.chunk_count} 个片段`);
            loadMaterials(); // 刷新列表更新状态
          }
        } catch (error) {
          console.error('存入RAG失败:', error);
          message.error('存入RAG失败');
        }
      },
    });
  };

  // 批量删除
  const handleBatchDelete = () => {
    if (selectedRowKeys.length === 0) {
      message.warning('请先选择要删除的素材');
      return;
    }
    
    Modal.confirm({
      title: '确认批量删除',
      content: `确定要删除选中的 ${selectedRowKeys.length} 个素材吗？此操作不可恢复。`,
      okText: '删除',
      okType: 'danger',
      cancelText: '取消',
      onOk: async () => {
        try {
          await Promise.all(
            selectedRowKeys.map(id => writingApi.deletePodcastMaterial(id))
          );
          message.success(`已删除 ${selectedRowKeys.length} 个素材`);
          setSelectedRowKeys([]);
          loadMaterials();
        } catch (error) {
          console.error('批量删除失败:', error);
          message.error('批量删除失败');
        }
      },
    });
  };

  // 生成播客文案
  const handleGenerateScript = async () => {
    if (selectedRowKeys.length === 0) {
      message.warning('请先选择至少一个素材');
      return;
    }
    
    setGenerating(true);
    try {
      const response = await writingApi.generatePodcastScript({
        material_ids: selectedRowKeys,
        prompt: prompt,
        model: selectedModel,
      });
      
      setGeneratedScript(response.script);
      message.success(`成功生成播客文案（基于${response.materials_count}个素材）`);
            
      // 检查是否保存到数据库
      console.log('[Podcast] ========== 文案生成成功 ==========');
      console.log('[Podcast] script_id:', response.script_metadata?.script_id);
      console.log('[Podcast] title:', response.script_metadata?.title);
      console.log('[Podcast] topic:', response.script_metadata?.topic);
      console.log('[Podcast] essay_type:', response.script_metadata?.essay_type);
      console.log('[Podcast] grade_level:', response.script_metadata?.grade_level);
      console.log('[Podcast] essay_style:', response.script_metadata?.essay_style);
      console.log('[Podcast] word_count:', response.script_metadata?.word_count);
      console.log('[Podcast] source:', response.script_metadata?.source);
      console.log('[Podcast] score:', response.script_metadata?.score);
      console.log('[Podcast] ======================================');
            
      if (response.script_metadata) {
        setCurrentScriptId(response.script_metadata.script_id);
        console.log('[Podcast] ✅ 文案已自动保存到数据库:', response.script_metadata.script_id);
        message.success(`✅ 文案已自动保存到“我的文案”`);
      } else {
        // 后端保存失败，提示用户手动保存
        console.warn('[Podcast] ⚠️ 文案未保存到数据库（script_metadata 为 null）');
        message.warning('⚠️ 文案生成成功，但未自动保存到数据库。请点击下方“保存到我的文案”按钮手动保存。', 5);
      }
      
      // 刷新文案列表（无论是否保存成功）
      loadScripts();
      
      // 清除旧的TTS分段数据，因为文案已更新
      setSavedAudioSegments([]);
      setAudioSegments([]);
      localStorage.removeItem('podcast_saved_segments');
      localStorage.removeItem('podcast_full_audio_url');
      console.log('生成新文案，清除旧的分段数据');
      
      // 刷新素材列表（更新状态）
      loadMaterials();
    } catch (error) {
      console.error('生成播客文案失败:', error);
      message.error('生成播客文案失败');
    } finally {
      setGenerating(false);
    }
  };

  // 手动保存文案到数据库
  const handleSaveScript = async () => {
    if (!generatedScript) {
      message.warning('没有可保存的文案');
      return;
    }
    
    try {
      console.log('[Podcast] 手动保存文案...');
      message.loading('正在保存...', 0);
      
      // 重新生成一次（后端会自动保存）
      const response = await writingApi.generatePodcastScript({
        material_ids: selectedRowKeys,
        prompt: prompt,
        model: selectedModel,
      });
      
      // 关闭loading
      message.destroy();
      
      if (response.script_metadata) {
        setCurrentScriptId(response.script_metadata.script_id);
        console.log('[Podcast] ✅ 文案已保存到数据库:', response.script_metadata.script_id);
        message.success(`✅ 文案已保存到“我的文案”`);
        loadScripts(); // 刷新列表
      } else {
        console.error('[Podcast] ❌ 保存失败，script_metadata 为 null');
        message.error('❌ 保存失败，请检查后端日志');
      }
    } catch (error) {
      message.destroy();
      console.error('[Podcast] 保存文案失败:', error);
      message.error('保存文案失败');
    }
  };

  // 打开TTS语音生成弹窗
  const handleOpenTtsModal = () => {
    if (!generatedScript) {
      message.warning('请先生成播客文案');
      return;
    }
    
    // 如果已有保存的分段数据，直接恢复
    if (savedAudioSegments.length > 0) {
      console.log('恢复之前保存的分段数据:', savedAudioSegments.length, '段');
      setAudioSegments(savedAudioSegments);
    } else {
      // 否则重新分段
      const segments = splitScriptIntoSegments(generatedScript);
      setAudioSegments(segments.map(text => ({
        text,
        status: 'pending' as const
      })));
    }
    
    setTtsModalVisible(true);
  };

  // 生成RSS Feed
  const handleGenerateRSS = async () => {
    // 如果没有选择任何文案，提示用户
    if (selectedScriptIds.length === 0) {
      Modal.confirm({
        title: '未选择文案',
        content: '您没有选择任何文案。是否生成所有已完成(completed)状态的文案的RSS Feed？',
        okText: '生成所有completed',
        cancelText: '取消',
        onOk: async () => {
          generateRSSWithIds(undefined); // 不传script_ids，后端会自动获取所有completed
        }
      });
      return;
    }
    
    // 有选择时，确认生成选中的文案
    Modal.confirm({
      title: '生成RSS Feed',
      content: `将为选中的 ${selectedScriptIds.length} 个文案生成RSS Feed，请确保这些文案都已标记为“完成”状态。`,
      okText: '确认生成',
      cancelText: '取消',
      onOk: async () => {
        generateRSSWithIds(selectedScriptIds);
      }
    });
  };

  // 实际生成RSS的函数
  const generateRSSWithIds = async (scriptIds?: string[]) => {
    setGeneratingRSS(true);
    try {
      const response = await writingApi.generatePodcastRSS({
        script_ids: scriptIds,
        limit: 100,
      });
      
      if (response.success && response.rss_xml) {
        setRssXmlContent(response.rss_xml);
        setRssDownloadUrl(response.download_url);
        setRssModalVisible(true);
        message.success(`✅ RSS Feed已生成，包含 ${response.count} 个文案`);
      } else {
        message.error('生成RSS失败');
      }
    } catch (error) {
      console.error('生成RSS失败:', error);
      message.error('生成RSS失败');
    } finally {
      setGeneratingRSS(false);
    }
  };

  // 复制RSS XML到剪贴板
  const handleCopyRSS = () => {
    if (!rssXmlContent) {
      message.warning('没有可复制的内容');
      return;
    }
    
    navigator.clipboard.writeText(rssXmlContent).then(() => {
      message.success('✅ RSS XML已复制到剪贴板');
    }).catch((error) => {
      console.error('复制失败:', error);
      message.error('复制失败');
    });
  };

  // 下载RSS XML文件
  const handleDownloadRSS = () => {
    if (!rssXmlContent) {
      message.warning('没有可下载的内容');
      return;
    }
    
    // 直接在前端创建Blob并下载，不依赖后端API
    const blob = new Blob([rssXmlContent], { type: 'application/xml;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `podcast_feed_${new Date().getTime()}.xml`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
    
    message.success('✅ RSS文件已下载');
  };

  // 将文案分割成段落（基于语义完整性）
  const splitScriptIntoSegments = (script: string): string[] => {
    // 按句号、感叹号、问号分割
    const sentences = script.split(/(?<=[。！？!?])/);
    
    // 合并短句，确保每段不超过60字
    const segments: string[] = [];
    let currentSegment = '';
    
    for (const sentence of sentences) {
      if ((currentSegment + sentence).length > 60 && currentSegment) {
        segments.push(currentSegment.trim());
        currentSegment = sentence;
      } else {
        currentSegment += sentence;
      }
    }
    
    if (currentSegment.trim()) {
      segments.push(currentSegment.trim());
    }
    
    return segments.filter(s => s.length > 0);
  };

  // 生成单个段落的语音
  const handleGenerateSegmentAudio = async (index: number) => {
    if (!savedRefAudioId) {
      message.warning('请先上传或选择参考音频');
      return;
    }
    
    // 【方案A】检查是否有当前文案ID，如果没有则无法自动关联
    if (!currentScriptId) {
      console.warn('[Podcast] ⚠️ 没有当前文案ID，音频将无法自动关联');
      message.warning({
        content: '⚠️ 请先保存播客文案，再生成音频（否则无法自动关联）',
        duration: 3,
      });
      return;
    }
    
    // 检查是否有 prompt_text（优先使用当前输入框的值，如果没有则从已保存的音频中获取）
    let finalPromptText = promptText.trim();
    
    if (!finalPromptText) {
      // 如果当前没有输入文本，尝试从已保存的音频中获取对应的文本
      const selectedAudio = refAudios.find(a => a.id === savedRefAudioId);
      if (selectedAudio && selectedAudio.prompt_text) {
        finalPromptText = selectedAudio.prompt_text;
        console.log('[TTS] 从已保存的音频中读取 prompt_text:', finalPromptText);
      } else {
        message.warning('请输入参考音频对应的文本，或从下拉菜单选择已保存的音频');
        return;
      }
    }
    
    console.log(`开始生成第 ${index + 1} 段语音...`);
    
    // 如果不是批量生成模式，设置全局loading状态
    const isBatchMode = ttsGenerating;
    if (!isBatchMode) {
      setTtsGenerating(true);
    }
    
    // 更新状态为生成中（使用函数式更新）
    setAudioSegments(prevSegments => {
      const updatedSegments = [...prevSegments];
      updatedSegments[index] = { ...prevSegments[index], status: 'generating' };
      return updatedSegments;
    });
    
    // 显示进度提示消息
    const progressMessage = message.loading(`第 ${index + 1} 段语音生成中...`, 0);
    
    // 模拟进度更新（每10秒更新一次提示）
    let progressStep = 0;
    const progressInterval = setInterval(() => {
      progressStep++;
      const steps = [
        '正在分析文本...',
        '正在合成语音...',
        '正在优化音质...',
        '即将完成...'
      ];
      const stepIndex = Math.min(progressStep - 1, steps.length - 1);
      console.log(`[进度] 第 ${index + 1} 段: ${steps[stepIndex]} (${progressStep * 10}秒)`);
    }, 10000); // 每10秒输出一次日志
    
    // 创建 AbortController 用于中止请求
    const abortController = new AbortController();
    setTtsAbortController(abortController);
    
    try {
      console.log('开始调用TTS API...');
      // 直接调用API，传入signal支持中止
      const response = await writingApi.generatePodcastTTS({
        text: audioSegments[index].text,  // 从当前状态获取文本
        ref_audio_id: savedRefAudioId,  // 使用已保存的音频ID
        prompt_text: finalPromptText,  // 使用最终确定的提示文本
        nfe,
        guidance_strength: guidanceStrength,
      }, abortController.signal);
      
      // 清除进度更新
      clearInterval(progressInterval);
      progressMessage();
      
      console.log('TTS响应:', response);
      console.log('音频URL:', response.audio_url);
      console.log('时长:', response.duration_sec);
      
      // 更新状态为完成（使用函数式更新）
      setAudioSegments(prevSegments => {
        const updatedSegments = [...prevSegments];
        updatedSegments[index] = {
          ...prevSegments[index],
          audio_url: response.audio_url,
          duration: response.duration_sec,
          status: 'completed'
        };
        return updatedSegments;
      });
      
      // 如果是最后一段，保存完整音频URL
      if (index === audioSegments.length - 1) {
        setFullAudioUrl(response.audio_url);
        console.log('所有段落生成完成，完整音频URL:', response.audio_url);
      }
      
      // 【方案A：完全自动化】每段音频生成后立即自动关联到文案
      if (currentScriptId && response.audio_url) {
        try {
          const audioId = response.audio_url.split('/').pop(); // 提取文件名
          await writingApi.addAudioAssociation(currentScriptId, {
            audio_id: audioId,
            segment_index: index + 1,  // 第几段
            duration: response.duration_sec,
          });
          console.log(`[Podcast] ✅ 第 ${index + 1} 段音频已自动关联到文案:`, currentScriptId);
        } catch (error) {
          console.error(`[Podcast] ❌ 第 ${index + 1} 段音频自动关联失败:`, error);
          // 不阻断流程，只记录错误
        }
      }
      
      console.log(`第 ${index + 1} 段语音生成完成`);
      
      // 显示成功消息
      message.success(`第 ${index + 1} 段语音生成成功！`);
      
      // 如果不是批量生成模式，重置loading状态
      if (!isBatchMode) {
        setTtsGenerating(false);
      }
    } catch (error: any) {
      // 清除进度更新
      clearInterval(progressInterval);
      progressMessage();
      
      // 如果是中止错误，不显示错误消息
      if (error.name === 'AbortError') {
        console.log('用户中生了TTS生成');
        setAudioSegments(prevSegments => {
          const updatedSegments = [...prevSegments];
          updatedSegments[index] = { ...prevSegments[index], status: 'pending' }; // 恢复为待生成状态
          return updatedSegments;
        });
        return;
      }
      
      console.error('生成语音失败:', error);
      console.error('错误详情:', error.response || error.message);
      
      // 更新状态为失败（使用函数式更新）
      setAudioSegments(prevSegments => {
        const updatedSegments = [...prevSegments];
        updatedSegments[index] = { ...prevSegments[index], status: 'failed' };
        return updatedSegments;
      });
      
      message.error(`第 ${index + 1} 段语音生成失败: ${error.message || '未知错误'}`);
      
      // 如果不是批量生成模式，重置loading状态
      if (!isBatchMode) {
        setTtsGenerating(false);
      }
    }
  };

  // 批量生成所有段落的语音
  const handleGenerateAllAudio = async () => {
    if (!savedRefAudioId) {
      message.warning('请先上传或选择参考音频');
      return;
    }
    
    // 检查是否有 prompt_text（优先使用当前输入框的值，如果没有则从已保存的音频中获取）
    let finalPromptText = promptText.trim();
    
    if (!finalPromptText) {
      // 如果当前没有输入文本，尝试从已保存的音频中获取对应的文本
      const selectedAudio = refAudios.find(a => a.id === savedRefAudioId);
      if (selectedAudio && selectedAudio.prompt_text) {
        finalPromptText = selectedAudio.prompt_text;
        console.log('[TTS] 从已保存的音频中读取 prompt_text:', finalPromptText);
      } else {
        message.warning('请输入参考音频对应的文本，或从下拉菜单选择已保存的音频');
        return;
      }
    }
    
    setTtsGenerating(true);
    
    // 显示文案合成中的提示
    const loadingMessage = message.loading('🎵 正在合成完整音频，请稍候...', 0);
    
    try {
      // 第一步：先生成完整合并音频（用于下载）
      console.log('[批量生成] 开始生成完整合并音频...');
      const fullText = audioSegments.map(seg => seg.text).join('');
      
      const fullResponse = await writingApi.generatePodcastTTS({
        text: fullText,
        ref_audio_id: savedRefAudioId,  // 使用已保存的音频ID
        prompt_text: finalPromptText,  // 使用最终确定的提示文本
        nfe,
        guidance_strength: guidanceStrength,
        is_full_audio: true,  // 标记为合并音频
      });
      
      // 关闭loading提示
      loadingMessage();
      message.success('✅ 完整音频合成完成，开始逐段生成...');
      
      // 保存完整音频URL（用于下载）
      setFullAudioUrl(fullResponse.audio_url);
      console.log('[批量生成] 完整合并音频生成完成:', fullResponse.audio_url);
      console.log('[批量生成] 完整音频时长:', fullResponse.duration_sec, '秒');
      
      // 第二步：逐段生成独立音频（用于试听），同时显示进度
      console.log('[批量生成] 开始逐段生成独立音频...');
      for (let i = 0; i < audioSegments.length; i++) {
        console.log(`[批量生成] 准备生成第 ${i + 1}/${audioSegments.length} 段...`);
        
        // 设置当前段为generating状态
        setAudioSegments(prevSegments => {
          const updated = [...prevSegments];
          updated[i] = { ...prevSegments[i], status: 'generating' as const };
          return updated;
        });
        
        // 调用单段生成API
        const segmentResponse = await writingApi.generatePodcastTTS({
          text: audioSegments[i].text,
          ref_audio_id: savedRefAudioId,  // 使用已保存的音频ID
          prompt_text: finalPromptText,  // 使用最终确定的提示文本
          nfe,
          guidance_strength: guidanceStrength,
        });
        
        // 更新当前段为completed状态
        setAudioSegments(prevSegments => {
          const updated = [...prevSegments];
          updated[i] = {
            ...prevSegments[i],
            audio_url: segmentResponse.audio_url,
            duration: segmentResponse.duration_sec,
            status: 'completed' as const
          };
          return updated;
        });
        
        console.log(`[批量生成] 第 ${i + 1} 段生成完成:`, segmentResponse.audio_url);
        message.success(`第 ${i + 1}/${audioSegments.length} 段语音生成成功！`);
      }
      
      console.log('[批量生成] 所有段落生成完成！');
      
      // 【方案A：完全自动化】显示最终提示
      message.success({
        content: `✅ 所有音频已自动生成、保存并关联到文案！`,
        duration: 3,
      });
      
    } catch (error) {
      // 确保关闭loading提示
      loadingMessage();
      console.error('[批量生成] 失败:', error);
      message.error('批量生成失败');
    } finally {
      // 确保总是重置 loading 状态
      setTtsGenerating(false);
    }
  };

  // 播放/暂停音频
  const handlePlayAudio = (index: number, audioUrl: string) => {
    if (currentPlayingIndex === index && audioPlayer) {
      // 暂停当前播放
      if (audioPlayer.paused) {
        audioPlayer.play();
      } else {
        audioPlayer.pause();
      }
    } else {
      // 停止之前的音频
      if (audioPlayer) {
        audioPlayer.pause();
        audioPlayer.currentTime = 0;
      }
      
      // 播放新音频
      const newAudio = new Audio(audioUrl);
      newAudio.onended = () => {
        setCurrentPlayingIndex(null);
        setAudioPlayer(null);
      };
      newAudio.onerror = () => {
        message.error('音频加载失败');
        setCurrentPlayingIndex(null);
        setAudioPlayer(null);
      };
      
      setCurrentPlayingIndex(index);
      setAudioPlayer(newAudio);
      newAudio.play().catch((err) => {
        console.error('播放失败:', err);
        message.error('播放失败');
        setCurrentPlayingIndex(null);
        setAudioPlayer(null);
      });
    }
  };

  // 下载完整音频（合并后的）
  const handleDownloadFullAudio = () => {
    // 优先使用完整音频URL
    const downloadUrl = fullAudioUrl || (audioSegments.find(s => s.status === 'completed' && s.audio_url)?.audio_url);
    
    if (!downloadUrl) {
      message.warning('没有可下载的音频');
      return;
    }
    
    const link = document.createElement('a');
    link.href = downloadUrl;
    link.download = `podcast_${new Date().getTime()}.wav`;
    link.click();
    message.success('开始下载完整音频');
  };

  // 下载单个分段音频
  const handleDownloadSegmentAudio = (index: number, audioUrl: string) => {
    const link = document.createElement('a');
    link.href = audioUrl;
    link.download = `podcast_segment_${String(index + 1).padStart(2, '0')}_${new Date().getTime()}.wav`;
    link.click();
    message.success(`开始下载第 ${index + 1} 段音频`);
  };

  // 获取阶段标签颜色
  const getStageColor = (stage: string) => {
    const colors: Record<string, string> = {
      analysis: 'blue',
      outline: 'green',
      essay: 'purple',
      evaluation: 'orange',
    };
    return colors[stage] || 'default';
  };

  // 获取阶段名称
  const getStageName = (stage: string) => {
    const names: Record<string, string> = {
      analysis: '审题分析',
      outline: '构思提纲',
      essay: '写作辅助',
      evaluation: '作文评估',
    };
    return names[stage] || stage;
  };

  // 表格列定义
  const columns = [
    {
      title: '阶段',
      key: 'stage',
      width: 120,
      render: (_: any, record: PodcastMaterial) => (
        <Tag color={getStageColor(record.stage)}>{getStageName(record.stage)}</Tag>
      ),
    },
    {
      title: '题目',
      dataIndex: 'topic',
      key: 'topic',
      width: 200,
      ellipsis: true,
    },
    {
      title: 'AI模型',
      dataIndex: 'ai_model',
      key: 'ai_model',
      width: 150,
      render: (model: string) => <Tag>{model}</Tag>,
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: string) => {
        const statusMap: Record<string, { color: string; text: string }> = {
          pending: { color: 'default', text: '待处理' },
          selected: { color: 'processing', text: '已选中' },
          imported: { color: 'success', text: '已导入' },
        };
        const config = statusMap[status] || { color: 'default', text: status };
        return <Badge color={config.color} text={config.text} />;
      },
    },
    {
      title: 'RAG状态',
      dataIndex: 'in_rag',
      key: 'in_rag',
      width: 120,
      render: (inRag: boolean) => {
        if (inRag) {
          return (
            <Tag icon={<DatabaseOutlined />} color="success">
              已存入RAG
            </Tag>
          );
        }
        return <Tag color="default">未存入</Tag>;
      },
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
      render: (time: string) => new Date(time).toLocaleString('zh-CN'),
    },
    {
      title: '操作',
      key: 'action',
      width: 280,
      fixed: 'right' as const,
      render: (_: any, record: PodcastMaterial) => (
        <Space size="small">
          <Button
            type="link"
            size="small"
            icon={<EyeOutlined />}
            onClick={() => handleView(record)}
          >
            查看
          </Button>
          <Button
            type="link"
            size="small"
            icon={<DownloadOutlined />}
            onClick={() => handleExport(record)}
          >
            导出
          </Button>
          {!record.in_rag && (
            <Button
              type="link"
              size="small"
              icon={<DatabaseOutlined />}
              onClick={() => handleAddToRag(record)}
              style={{ color: '#52c41a' }}
            >
              存入RAG
            </Button>
          )}
          <Button
            type="link"
            size="small"
            danger
            icon={<DeleteOutlined />}
            onClick={() => handleDelete(record.id)}
          >
            删除
          </Button>
        </Space>
      ),
    },
  ];

  return (
    <div style={{ padding: '24px' }}>
      <Card>
        <div style={{ marginBottom: 24 }}>
          <Title level={2}>
            <SoundOutlined /> 播客模块
          </Title>
          <Text type="secondary">
            管理播客素材和文案，生成语音内容。
          </Text>
        </div>

        {/* Tabs 标签页 */}
        <Tabs activeKey={activeTab} onChange={(key) => setActiveTab(key as 'materials' | 'scripts')}>
          {/* 素材库标签页 */}
          <Tabs.TabPane tab="素材库" key="materials">

        {/* 统计信息 */}
        <Space size="large" style={{ marginBottom: 16 }}>
          <div>
            <Text type="secondary">总素材数：</Text>
            <Text strong style={{ fontSize: 18, color: '#1890ff' }}>{materials.length}</Text>
          </div>
          <div>
            <Text type="secondary">审题分析：</Text>
            <Text strong>{materials.filter(m => m.stage === 'analysis').length}</Text>
          </div>
          <div>
            <Text type="secondary">构思提纲：</Text>
            <Text strong>{materials.filter(m => m.stage === 'outline').length}</Text>
          </div>
          <div>
            <Text type="secondary">写作辅助：</Text>
            <Text strong>{materials.filter(m => m.stage === 'essay').length}</Text>
          </div>
          <div>
            <Text type="secondary">作文评估：</Text>
            <Text strong>{materials.filter(m => m.stage === 'evaluation').length}</Text>
          </div>
        </Space>

        {/* 素材列表 */}
        <div style={{ marginBottom: 16 }}>
          <Space>
            <Button
              type="primary"
              icon={<StarOutlined />}
              onClick={() => setGenerateModalVisible(true)}
              disabled={selectedRowKeys.length === 0}
              style={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }}
            >
              生成播客文案 ({selectedRowKeys.length})
            </Button>
            <Button
              danger
              icon={<DeleteOutlined />}
              onClick={handleBatchDelete}
              disabled={selectedRowKeys.length === 0}
            >
              批量删除 ({selectedRowKeys.length})
            </Button>
          </Space>
        </div>

        <Table
          columns={columns}
          dataSource={materials}
          rowKey="id"
          loading={loading}
          pagination={{ pageSize: 10 }}
          scroll={{ x: 1200 }}
          rowSelection={{
            selectedRowKeys,
            onChange: (keys) => setSelectedRowKeys(keys as string[]),
          }}
          locale={{
            emptyText: (
              <Empty
                image={Empty.PRESENTED_IMAGE_SIMPLE}
                description={
                  <div>
                    <Text type="secondary">暂无播客素材</Text>
                    <br />
                    <Text type="secondary" style={{ fontSize: 12 }}>
                      请前往写作训练页面，使用【一键生成播客素材】功能
                    </Text>
                  </div>
                }
              />
            ),
          }}
        />
          </Tabs.TabPane>

          {/* 我的文案标签页 */}
          <Tabs.TabPane tab={`我的文案 (${scriptList.length})`} key="scripts">
            {/* RSS功能按钮和筛选器 */}
            <div style={{ marginBottom: 16 }}>
              <Space wrap>
                <Button
                  type="primary"
                  icon={<SoundOutlined />}
                  onClick={handleGenerateRSS}
                  loading={generatingRSS}
                >
                  生成RSS Feed
                </Button>
                
                {selectedScriptIds.length > 0 && (
                  <Tag color="blue">已选择 {selectedScriptIds.length} 个文案</Tag>
                )}
                
                <Text>阶段：</Text>
                <Select
                  style={{ width: 120 }}
                  placeholder="全部阶段"
                  allowClear
                  value={stageFilter}
                  onChange={(value) => setStageFilter(value)}
                >
                  <Option value="shenti">审题分析</Option>
                  <Option value="gousi">构思提纲</Option>
                  <Option value="xiezuo">写作辅助</Option>
                  <Option value="pinggu">写作评估</Option>
                </Select>
                
                <Text>状态：</Text>
                <Select
                  style={{ width: 100 }}
                  placeholder="全部状态"
                  allowClear
                  value={statusFilter}
                  onChange={(value) => setStatusFilter(value)}
                >
                  <Option value="draft">草稿</Option>
                  <Option value="completed">完成</Option>
                  <Option value="archived">归档</Option>
                </Select>
                
                <Text type="secondary" style={{ fontSize: 12 }}>
                  将已完成的文案生成为RSS Feed，可提交到小宇宙等播客平台
                </Text>
              </Space>
            </div>
            
            {/* Table组件展示文案列表 */}
            <Table
              rowSelection={{
                selectedRowKeys: selectedScriptIds,
                onChange: (keys) => setSelectedScriptIds(keys as string[])
              }}
              columns={[
                {
                  title: '阶段',
                  dataIndex: 'stage',
                  key: 'stage',
                  width: 100,
                  render: (stage: string, record: PodcastScript) => (
                    <Space>
                      {(() => {
                        const stageMap: Record<string, { text: string; color: string }> = {
                          shenti: { text: '审题分析', color: 'blue' },
                          gousi: { text: '构思提纲', color: 'green' },
                          xiezuo: { text: '写作辅助', color: 'orange' },
                          pinggu: { text: '写作评估', color: 'purple' }
                        };
                        const config = stageMap[stage] || { text: '未设置', color: 'default' };
                        return <Tag color={config.color}>{config.text}</Tag>;
                      })()}
                      <Button 
                        type="link" 
                        size="small"
                        icon={<EditOutlined />}
                        onClick={() => handleOpenStageModal(record.script_id, record.stage)}
                      />
                    </Space>
                  )
                },
                {
                  title: '题目类型',
                  dataIndex: 'essay_type',
                  key: 'essay_type',
                  width: 120,
                  ellipsis: true,
                  render: (text: string) => text || '-'
                },
                {
                  title: '学段',
                  dataIndex: 'grade_level',
                  key: 'grade_level',
                  width: 100,
                  render: (text: string) => text || '-'
                },
                {
                  title: '题目',
                  dataIndex: 'topic',
                  key: 'topic',
                  width: 200,
                  ellipsis: true,
                  render: (text: string) => text || '-'
                },
                {
                  title: '文体',
                  dataIndex: 'essay_style',
                  key: 'essay_style',
                  width: 120,
                  render: (text: string) => text || '-'
                },
                {
                  title: '版本',
                  key: 'version',
                  width: 80,
                  render: (_: any, record: PodcastScript) => (
                    record.version > 1 ? <Tag color="blue">v{record.version}</Tag> : '-'
                  )
                },
                {
                  title: '音频',
                  key: 'audio',
                  width: 120,
                  render: (_: any, record: PodcastScript) => (
                    <Space>
                      {record.has_audio ? (
                        <Badge status="success" text={`已关联(${record.audio_count})`} />
                      ) : (
                        <Badge status="default" text="待关联" />
                      )}
                      {!record.has_audio && (
                        <Button 
                          type="link" 
                          size="small"
                          icon={<EditOutlined />}
                          onClick={() => handleOpenAudioModal(record.script_id)}
                        >
                          关联
                        </Button>
                      )}
                    </Space>
                  )
                },
                {
                  title: 'RAG状态',
                  key: 'rag',
                  width: 120,
                  render: (_: any, record: PodcastScript) => (
                    <Space>
                      {record.in_rag ? (
                        <Tag color="green">已加入</Tag>
                      ) : (
                        <>
                          <Tag color="default">未加入</Tag>
                          <Button 
                            type="link" 
                            size="small"
                            onClick={() => handleAddScriptToRag(record.script_id)}
                          >
                            加入
                          </Button>
                        </>
                      )}
                    </Space>
                  )
                },
                {
                  title: '状态',
                  dataIndex: 'status',
                  key: 'status',
                  width: 80,
                  render: (status: string) => (
                    <Tag color={status === 'completed' ? 'green' : status === 'draft' ? 'orange' : 'default'}>
                      {status === 'draft' ? '草稿' : status === 'completed' ? '完成' : '归档'}
                    </Tag>
                  )
                },
                {
                  title: '创建时间',
                  dataIndex: 'created_at',
                  key: 'created_at',
                  width: 180,
                  sorter: (a: PodcastScript, b: PodcastScript) => (a.created_at || '').localeCompare(b.created_at || '')
                },
                {
                  title: '操作',
                  key: 'action',
                  width: 280,
                  fixed: 'right',
                  render: (_: any, record: PodcastScript) => (
                    <Space size="small">
                      <Button 
                        type="link" 
                        size="small"
                        icon={<EditOutlined />}
                        onClick={() => handleOpenScript(record)}
                      >
                        打开
                      </Button>
                      {record.status !== 'completed' && (
                        <Button 
                          type="link" 
                          size="small"
                          style={{ color: '#52c41a' }}
                          onClick={() => handleUpdateScriptStatus(record.script_id, 'completed')}
                        >
                          标记为完成
                        </Button>
                      )}
                      <Button 
                        type="link" 
                        size="small"
                        icon={<CopyOutlined />}
                        onClick={() => handleDuplicateScript(record)}
                      >
                        复制
                      </Button>
                      <Button 
                        type="link" 
                        size="small"
                        danger
                        icon={<DeleteOutlined />}
                        onClick={() => handleDeleteScript(record.script_id)}
                      >
                        删除
                      </Button>
                    </Space>
                  )
                }
              ]}
              dataSource={scriptList}
              rowKey="script_id"
              loading={loadingScripts}
              pagination={{
                current: scriptPage,
                pageSize: scriptPageSize,
                showSizeChanger: true,
                showQuickJumper: true,
                showTotal: (total) => `共 ${total} 条`,
                pageSizeOptions: ['10', '20', '50', '100'],
                onChange: (page, pageSize) => {
                  setScriptPage(page);
                  setScriptPageSize(pageSize);
                }
              }}
              scroll={{ x: 1200 }}
              locale={{
                emptyText: (
                  <Empty
                    image={Empty.PRESENTED_IMAGE_SIMPLE}
                    description={
                      <Text type="secondary">
                        暂无文案，请在“素材库”中选择素材后生成文案
                      </Text>
                    }
                  />
                )
              }}
            />
          </Tabs.TabPane>
        </Tabs>
      </Card>

      {/* 查看详情弹窗 */}
      <Modal
        title={
          <Space>
            <SoundOutlined />
            <span>素材详情</span>
          </Space>
        }
        open={viewModalVisible}
        onCancel={() => setViewModalVisible(false)}
        footer={[
          <Button key="close" onClick={() => setViewModalVisible(false)}>
            关闭
          </Button>,
          <Button
            key="export"
            type="primary"
            icon={<DownloadOutlined />}
            onClick={() => selectedMaterial && handleExport(selectedMaterial)}
          >
            导出
          </Button>,
        ]}
        width={800}
      >
        {selectedMaterial && (
          <div>
            <div style={{ marginBottom: 16 }}>
              <Text strong>阶段：</Text>
              <Tag color={getStageColor(selectedMaterial.stage)}>
                {getStageName(selectedMaterial.stage)}
              </Tag>
            </div>
            <div style={{ marginBottom: 16 }}>
              <Text strong>题目：</Text>
              <Text>{selectedMaterial.topic}</Text>
            </div>
            <div style={{ marginBottom: 16 }}>
              <Text strong>AI模型：</Text>
              <Tag>{selectedMaterial.ai_model}</Tag>
            </div>
            <div style={{ marginBottom: 16 }}>
              <Text strong>创建时间：</Text>
              <Text>{new Date(selectedMaterial.created_at).toLocaleString('zh-CN')}</Text>
            </div>
            <div style={{ marginBottom: 16 }}>
              <Text strong>状态：</Text>
              <Badge 
                color={selectedMaterial.status === 'imported' ? 'success' : 'default'} 
                text={selectedMaterial.status} 
              />
            </div>
            <div style={{ marginTop: 24 }}>
              <Text strong>内容：</Text>
              <div
                style={{
                  marginTop: 8,
                  padding: 16,
                  background: '#f5f5f5',
                  borderRadius: 4,
                  maxHeight: 400,
                  overflow: 'auto',
                }}
              >
                <Paragraph style={{ whiteSpace: 'pre-wrap' }}>
                  {selectedMaterial.content}
                </Paragraph>
              </div>
            </div>
          </div>
        )}
      </Modal>

      {/* 生成播客文案弹窗 */}
      <Modal
        title={
          <Space>
            <StarOutlined style={{ color: '#722ed1' }} />
            <span>生成播客文案</span>
          </Space>
        }
        open={generateModalVisible}
        onCancel={() => {
          setGenerateModalVisible(false);
          setGeneratedScript('');
        }}
        footer={[
          <Button key="close" onClick={() => {
            setGenerateModalVisible(false);
            setGeneratedScript('');
          }}>
            关闭
          </Button>,
          <Button
            key="generate"
            type="primary"
            icon={<StarOutlined />}
            onClick={handleGenerateScript}
            loading={generating}
            disabled={selectedRowKeys.length === 0}
          >
            {generating ? '生成中...' : '生成播客文案'}
          </Button>,
          generatedScript && (
            <Button
              key="tts"
              type="default"
              icon={<SoundOutlined />}
              onClick={handleOpenTtsModal}
              style={{ background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)', color: 'white' }}
            >
              转语音
            </Button>
          ),
          generatedScript && (
            <Button
              key="export"
              type="default"
              icon={<DownloadOutlined />}
              onClick={() => {
                const blob = new Blob([generatedScript], { type: 'text/plain;charset=utf-8' });
                const url = URL.createObjectURL(blob);
                const link = document.createElement('a');
                link.href = url;
                link.download = `podcast_script_${new Date().getTime()}.txt`;
                link.click();
                URL.revokeObjectURL(url);
                message.success('已导出播客文案');
              }}
            >
              导出文案
            </Button>
          ),
          generatedScript && (
            <Button
              key="save"
              type="primary"
              icon={<SaveOutlined />}
              onClick={handleSaveScript}
              disabled={!!currentScriptId} // 如果已经有 script_id，说明已经保存过，禁用按钮
              style={{ background: 'linear-gradient(135deg, #52c41a 0%, #73d13d 100%)' }}
            >
              {currentScriptId ? '✅ 已保存' : '💾 保存到我的文案'}
            </Button>
          ),
        ].filter(Boolean)}
        width={900}
      >
        {!generatedScript ? (
          <div>
            <div style={{ marginBottom: 16 }}>
              <Text strong>已选素材：</Text>
              <Tag color="blue">{selectedRowKeys.length} 个</Tag>
            </div>
            
            <div style={{ marginBottom: 16 }}>
              <Text strong>选择模型：</Text>
              <Select
                value={selectedModel}
                onChange={setSelectedModel}
                style={{ width: 200, marginLeft: 8 }}
              >
                <Option value="qwen3:8b">qwen3:8b (推荐)</Option>
                <Option value="gemma3:4b">gemma3:4b (快速)</Option>
              </Select>
            </div>

            <div style={{ marginBottom: 16 }}>
              <Text strong>提示词：</Text>
              <TextArea
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                rows={4}
                placeholder="请输入生成播客文案的提示词..."
                style={{ marginTop: 8 }}
              />
              <Text type="secondary" style={{ fontSize: 12, marginTop: 4, display: 'block' }}>
                提示：可以指定风格、长度、语气等要求
              </Text>
            </div>

            <div style={{ padding: 12, background: '#f0f5ff', borderRadius: 4 }}>
              <Text type="secondary">
                💡 系统将基于选中的素材，使用AI生成一段生动有趣的播客对话。
              </Text>
            </div>
          </div>
        ) : (
          <div>
            <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <Badge count="成功" style={{ backgroundColor: '#52c41a' }} />
                <Text strong style={{ marginLeft: 8 }}>播客文案已生成！</Text>
              </div>
              <Button
                danger
                icon={<DeleteOutlined />}
                onClick={() => {
                  Modal.confirm({
                    title: '确认清空文案？',
                    content: '清空后需要重新生成，确定要清空吗？',
                    okText: '确认清空',
                    cancelText: '取消',
                    okType: 'danger',
                    onOk: async () => {
                      // 如果有 script_id，调用后端 API 删除
                      if (currentScriptId) {
                        try {
                          await writingApi.deletePodcastScript(currentScriptId);
                          message.success('文案已从数据库中删除');
                          loadScripts(); // 刷新列表
                        } catch (error) {
                          console.error('删除文案失败:', error);
                          message.error('删除文案失败');
                        }
                      }
                      
                      setGeneratedScript('');
                      setCurrentScriptId(null);
                      setSavedAudioSegments([]);
                      setAudioSegments([]);
                      setFullAudioUrl(null);
                      
                      // 清除 localStorage（兼容旧数据）
                      try {
                        localStorage.removeItem('podcast_generated_script');
                        localStorage.removeItem('podcast_saved_segments');
                        localStorage.removeItem('podcast_full_audio_url');
                        console.log('[Podcast] 已清除 localStorage 数据');
                      } catch (error) {
                        console.error('[Podcast] 清除 localStorage 失败:', error);
                      }
                      
                      message.success('文案已清空');
                    }
                  });
                }}
              >
                清空文案
              </Button>
            </div>
            <div
              style={{
                padding: 16,
                background: '#fafafa',
                borderRadius: 4,
                maxHeight: 500,
                overflow: 'auto',
              }}
            >
              <Paragraph style={{ whiteSpace: 'pre-wrap', lineHeight: 1.8 }}>
                {generatedScript}
              </Paragraph>
            </div>
          </div>
        )}
      </Modal>

      {/* TTS语音生成弹窗 */}
      <Modal
        title={
          <Space>
            <SoundOutlined style={{ color: '#f5576c' }} />
            <span>文案转语音 (TTS)</span>
          </Space>
        }
        open={ttsModalVisible}
        onCancel={() => {
          // 关闭时保存当前的分段数据
          setSavedAudioSegments(audioSegments);
          console.log('关闭TTS弹窗，保存分段数据:', audioSegments.length, '段');
          
          // 保存到 localStorage
          try {
            localStorage.setItem('podcast_saved_segments', JSON.stringify(audioSegments));
            if (fullAudioUrl) {
              localStorage.setItem('podcast_full_audio_url', fullAudioUrl);
            }
            console.log('[Podcast] 分段数据已保存到 localStorage');
          } catch (error) {
            console.error('[Podcast] 保存分段数据失败:', error);
          }
          
          setTtsModalVisible(false);
          setRefAudioFile(null);
          setCurrentPlayingIndex(null);
          // 不清空 audioSegments 和 fullAudioUrl，下次打开时恢复
        }}
        footer={[
          <Button key="close" onClick={() => {
            // 关闭时保存当前的分段数据
            setSavedAudioSegments(audioSegments);
            console.log('点击关闭按钮，保存分段数据:', audioSegments.length, '段');
            
            // 保存到 localStorage
            try {
              localStorage.setItem('podcast_saved_segments', JSON.stringify(audioSegments));
              if (fullAudioUrl) {
                localStorage.setItem('podcast_full_audio_url', fullAudioUrl);
              }
              console.log('[Podcast] 分段数据已保存到 localStorage');
            } catch (error) {
              console.error('[Podcast] 保存分段数据失败:', error);
            }
            
            setTtsModalVisible(false);
            setRefAudioFile(null);
            setCurrentPlayingIndex(null);
            // 不清空 audioSegments 和 fullAudioUrl，下次打开时恢复
          }}>
            关闭
          </Button>,
          ttsGenerating && (
            <Button
              key="abort"
              danger
              icon={<StopOutlined />}
              onClick={handleAbortTTS}
            >
              中止生成
            </Button>
          ),
          <Button
            key="generate-all"
            type="primary"
            icon={<CloudUploadOutlined />}
            onClick={handleGenerateAllAudio}
            loading={ttsGenerating}
            disabled={!savedRefAudioId || audioSegments.length === 0 || ttsGenerating}
          >
            {ttsGenerating ? '生成中...' : '批量生成所有段落'}
          </Button>,
          audioSegments.some(s => s.status === 'completed') && (
            <Button
              key="download"
              type="default"
              icon={<DownloadOutlined />}
              onClick={handleDownloadFullAudio}
            >
              下载音频
            </Button>
          ),
        ].filter(Boolean)}
        width={1000}
      >
        <div>
          {/* 配置区域 */}
          <Card size="small" title="语音配置" style={{ marginBottom: 16 }}>
            <Space direction="vertical" style={{ width: '100%' }}>
              {/* 上传参考音频 */}
              <div>
                <Text strong>1. 上传参考音频（3-8秒）：</Text>
                <Upload
                  accept="audio/*"
                  maxCount={1}
                  beforeUpload={(file) => {
                    // 只保存到前端状态，不立即上传到服务器
                    setRefAudioFile(file);
                    message.success(`已选择文件: ${file.name}，请输入文本后点击“保存角色”`);
                    return false; // 阻止默认上传行为
                  }}
                  onRemove={() => {
                    setRefAudioFile(null);
                  }}
                >
                  <Button icon={<CloudUploadOutlined />}>
                    选择音频文件
                  </Button>
                </Upload>
                {refAudioFile && (
                  <Text style={{ marginTop: 8, display: 'block' }}>
                    ✓ 已选择: {refAudioFile.name}
                  </Text>
                )}
                {savedRefAudioId && !refAudioFile && (
                  <Text type="success" style={{ marginTop: 8, display: 'block' }}>
                    ✓ 已选择: {refAudios.find(a => a.id === savedRefAudioId)?.name || '已保存的音频'}
                  </Text>
                )}
              </div>

              {/* 选择已保存的参考音频 */}
              {refAudios.length > 0 && (
                <div style={{ marginTop: 12 }}>
                  <Text strong>或从历史音频中选择：</Text>
                  <Select
                    value={savedRefAudioId || undefined}
                    onChange={(value) => {
                      setSavedRefAudioId(value);
                      localStorage.setItem('podcast_ref_audio_id', value);
                      
                      // 自动填充对应的文本
                      const selectedAudio = refAudios.find(a => a.id === value);
                      if (selectedAudio && selectedAudio.prompt_text) {
                        setPromptText(selectedAudio.prompt_text);
                        message.success(`已切换参考音频，并自动填充文本`);
                      } else {
                        message.success('已切换参考音频');
                      }
                    }}
                    style={{ width: '100%', marginTop: 8 }}
                    placeholder="选择一个已保存的参考音频"
                    loading={loadingRefAudios}
                    allowClear
                    onClear={() => {
                      setSavedRefAudioId(null);
                      localStorage.removeItem('podcast_ref_audio_id');
                    }}
                  >
                    {refAudios.map(audio => (
                      <Select.Option key={audio.id} value={audio.id}>
                        <Space>
                          <span>{audio.name}</span>
                          <Button
                            size="small"
                            type="text"
                            danger
                            onClick={(e) => {
                              e.stopPropagation();
                              Modal.confirm({
                                title: '确认删除？',
                                content: `确定要删除音频 "${audio.name}" 吗？`,
                                okText: '删除',
                                okType: 'danger',
                                cancelText: '取消',
                                onOk: async () => {
                                  try {
                                    await writingApi.deleteRefAudio(audio.id);
                                    message.success('已删除');
                                    loadRefAudios();
                                    if (savedRefAudioId === audio.id) {
                                      setSavedRefAudioId(null);
                                      localStorage.removeItem('podcast_ref_audio_id');
                                    }
                                  } catch (error) {
                                    console.error('删除失败:', error);
                                    message.error('删除失败');
                                  }
                                }
                              });
                            }}
                          >
                            删除
                          </Button>
                        </Space>
                      </Select.Option>
                    ))}
                  </Select>
                </div>
              )}

              <Divider style={{ margin: '12px 0' }} />

              {/* 参考音频对应的文本 */}
              <div>
                <Text strong>2. 参考音频文本（用于对齐音色）：</Text>
                <TextArea
                  value={promptText}
                  onChange={(e) => setPromptText(e.target.value)}
                  rows={2}
                  placeholder="请输入参考音频中说的文本内容..."
                  style={{ marginTop: 8 }}
                />
                <Text type="secondary" style={{ fontSize: 12, marginTop: 4, display: 'block' }}>
                  💡 提示：输入参考音频对应的文本，有助于提高音色克隆质量
                </Text>
              </div>

              {/* 保存角色按钮 */}
              {(refAudioFile || savedRefAudioId) && (
                <div style={{ marginTop: 12 }}>
                  <Button
                    type="primary"
                    icon={<SaveOutlined />}
                    onClick={async () => {
                      if (!promptText.trim()) {
                        message.warning('请先输入参考音频对应的文本');
                        return;
                      }
                      
                      // 如果是新上传的音频，先上传到服务器
                      if (refAudioFile) {
                        try {
                          message.loading('正在保存角色...', 0);
                          const response = await writingApi.uploadRefAudio(refAudioFile, promptText);
                          message.destroy();
                          
                          setSavedRefAudioId(response.id);
                          localStorage.setItem('podcast_ref_audio_id', response.id);
                          setRefAudioFile(null); // 清除临时文件
                          message.success(`✅ 角色已保存: ${response.name}`);
                          
                          // 刷新列表
                          loadRefAudios();
                        } catch (error) {
                          message.destroy();
                          console.error('保存角色失败:', error);
                          message.error('保存失败');
                        }
                      } else {
                        // 如果只是修改了文本，更新已保存的角色的文本
                        if (savedRefAudioId) {
                          try {
                            message.loading('正在更新文本...', 0);
                            await writingApi.updateRefAudioText(savedRefAudioId, promptText);
                            message.destroy();
                            message.success('✅ 文本已更新');
                            
                            // 刷新列表
                            loadRefAudios();
                          } catch (error) {
                            message.destroy();
                            console.error('更新文本失败:', error);
                            message.error('更新失败');
                          }
                        }
                      }
                    }}
                    block
                  >
                    保存角色（音频 + 文本）
                  </Button>
                </div>
              )}

              <Divider style={{ margin: '12px 0' }} />

              {/* 分段模式选择 */}
              <div>
                <Text strong>3. 分段模式：</Text>
                <Select
                  value={ttsMode}
                  onChange={setTtsMode}
                  style={{ width: 200, marginLeft: 8 }}
                >
                  <Option value="precise">精准模式 (30字/段)</Option>
                  <Option value="standard">标准模式 (45字/段)</Option>
                  <Option value="fast">快速模式 (60字/段)</Option>
                </Select>
                <Text type="secondary" style={{ marginLeft: 8, fontSize: 12 }}>
                  {ttsMode === 'precise' && '适合重要内容，质量最高'}
                  {ttsMode === 'standard' && '默认推荐，平衡质量和效率'}
                  {ttsMode === 'fast' && '适合草稿，减少拼接工作量'}
                </Text>
              </div>

              <Divider style={{ margin: '12px 0' }} />

              {/* 高级参数（可折叠） */}
              <div>
                <Text strong>4. 高级参数（可选）：</Text>
                <Space size="large" style={{ marginTop: 8 }}>
                  <div>
                    <Text>NFE步数：</Text>
                    <Input
                      type="number"
                      min={10}
                      max={30}
                      value={nfe}
                      onChange={(e) => setNfe(Number(e.target.value))}
                      style={{ width: 80, marginLeft: 8 }}
                    />
                    <Text type="secondary" style={{ fontSize: 12, marginLeft: 4 }}>(推荐22-25，越高音质越好但速度越慢)</Text>
                  </div>
                  <div>
                    <Text>引导强度：</Text>
                    <Input
                      type="number"
                      min={2.0}
                      max={5.0}
                      step={0.1}
                      value={guidanceStrength}
                      onChange={(e) => setGuidanceStrength(Number(e.target.value))}
                      style={{ width: 80, marginLeft: 8 }}
                    />
                    <Text type="secondary" style={{ fontSize: 12, marginLeft: 4 }}>(推荐2.5-3.2，过高会破音)</Text>
                  </div>
                </Space>
              </div>
            </Space>
          </Card>

          {/* 分段列表 */}
          <div>
            <Text strong>分段预览（共 {audioSegments.length} 段）：</Text>
            <div style={{ maxHeight: 500, overflow: 'auto', marginTop: 12 }}>
              {audioSegments.map((segment, index) => (
                <Card
                  key={index}
                  size="small"
                  style={{
                    marginBottom: 12,
                    borderLeft: segment.status === 'completed' ? '4px solid #52c41a' :
                                segment.status === 'generating' ? '4px solid #1890ff' :
                                segment.status === 'failed' ? '4px solid #ff4d4f' :
                                '4px solid #d9d9d9'
                  }}
                >
                  <Space direction="vertical" style={{ width: '100%' }}>
                    {/* 段落文本（可编辑） */}
                    <div>
                      <Badge count={index + 1} style={{ backgroundColor: '#722ed1' }} />
                      <TextArea
                        value={segment.text}
                        onChange={(e) => {
                          const updatedSegments = [...audioSegments];
                          updatedSegments[index] = { ...segment, text: e.target.value };
                          setAudioSegments(updatedSegments);
                        }}
                        rows={3}
                        style={{ marginTop: 8, fontSize: 14 }}
                        placeholder="请输入或修改文案内容..."
                      />
                      <Text type="secondary" style={{ marginLeft: 8, fontSize: 12 }}>
                        ({segment.text.length}字)
                      </Text>
                    </div>

                    {/* 状态和操作 */}
                    <Space>
                      {segment.status === 'pending' && (
                        <Tag color="default">待生成</Tag>
                      )}
                      {segment.status === 'generating' && (
                        <Tag color="processing">生成中...</Tag>
                      )}
                      {segment.status === 'completed' && (
                        <Tag color="success">✓ 已完成</Tag>
                      )}
                      {segment.status === 'failed' && (
                        <Tag color="error">✗ 失败</Tag>
                      )}

                      {segment.duration && (
                        <Text type="secondary">
                          时长: {segment.duration.toFixed(1)}秒
                        </Text>
                      )}

                      {/* 操作按钮 */}
                      <Space size="small">
                        <Button
                          size="small"
                          type="primary"
                          onClick={() => handleGenerateSegmentAudio(index)}
                          disabled={!savedRefAudioId || segment.status === 'generating'}
                          loading={segment.status === 'generating'}
                        >
                          {segment.status === 'completed' ? '重新生成' : '生成语音'}
                        </Button>

                        {segment.status === 'completed' && segment.audio_url && (
                          <Space size="small">
                            <Button
                              size="small"
                              icon={currentPlayingIndex === index ? <PauseCircleOutlined /> : <PlayCircleOutlined />}
                              onClick={() => handlePlayAudio(index, segment.audio_url!)}
                            >
                              {currentPlayingIndex === index ? '暂停' : '试听'}
                            </Button>
                            
                            <Button
                              size="small"
                              icon={<DownloadOutlined />}
                              onClick={() => handleDownloadSegmentAudio(index, segment.audio_url!)}
                            >
                              下载
                            </Button>
                          </Space>
                        )}
                      </Space>
                    </Space>
                  </Space>
                </Card>
              ))}
            </div>
          </div>

          {/* 进度提示 */}
          {audioSegments.length > 0 && (
            <div style={{ marginTop: 16 }}>
              <Progress
                percent={Math.round(
                  (audioSegments.filter(s => s.status === 'completed').length / audioSegments.length) * 100
                )}
                status={ttsGenerating ? 'active' : undefined}
              />
              <Text type="secondary" style={{ fontSize: 12 }}>
                已完成: {audioSegments.filter(s => s.status === 'completed').length} / {audioSegments.length}
              </Text>
              
              {/* 批量操作按钮 */}
              {!ttsGenerating && audioSegments.some(s => s.status === 'completed') && (
                <Space style={{ marginTop: 12 }}>
                  <Button
                    size="small"
                    icon={<DownloadOutlined />}
                    onClick={handleDownloadFullAudio}
                    disabled={!fullAudioUrl && !audioSegments.some(s => s.status === 'completed' && s.audio_url)}
                  >
                    下载完整合并音频
                  </Button>
                  <Button
                    size="small"
                    onClick={() => {
                      // 批量下载所有分段
                      const completedSegments = audioSegments.filter(s => s.status === 'completed' && s.audio_url);
                      completedSegments.forEach((s, idx) => {
                        setTimeout(() => handleDownloadSegmentAudio(audioSegments.indexOf(s), s.audio_url!), idx * 500);
                      });
                      message.success(`开始批量下载 ${completedSegments.length} 个分段音频`);
                    }}
                  >
                    批量下载所有分段
                  </Button>
                </Space>
              )}
            </div>
          )}
        </div>
      </Modal>

      {/* RSS Feed弹窗 */}
      <Modal
        title={
          <Space>
            <SoundOutlined />
            <span>RSS Feed</span>
          </Space>
        }
        open={rssModalVisible}
        onCancel={() => setRssModalVisible(false)}
        footer={[
          <Button key="close" onClick={() => setRssModalVisible(false)}>
            关闭
          </Button>,
          <Button
            key="copy"
            icon={<CopyOutlined />}
            onClick={handleCopyRSS}
          >
            复制XML
          </Button>,
          <Button
            key="download"
            type="primary"
            icon={<DownloadOutlined />}
            onClick={handleDownloadRSS}
          >
            下载XML文件
          </Button>,
        ]}
        width={900}
      >
        <div>
          <Alert
            message="✅ RSS Feed已生成"
            description={
              <div>
                <p>此RSS Feed包含 <strong>{scriptList.filter(s => s.status === 'completed').length}</strong> 个已完成的播客文案。</p>
                <p style={{ marginTop: 8 }}>
                  <strong>如何提交到小宇宙：</strong>
                  <ol style={{ paddingLeft: 20, marginTop: 4 }}>
                    <li>点击“下载XML文件”按钮，保存RSS文件</li>
                    <li>将文件上传到你的网站或云存储（需要公开可访问的URL）</li>
                    <li>在小宇宙APP中，使用“订阅”功能输入RSS URL</li>
                    <li>等待审核通过后即可发布</li>
                  </ol>
                </p>
              </div>
            }
            type="success"
            showIcon
            style={{ marginBottom: 16 }}
          />
          
          <Text strong>RSS XML预览：</Text>
          <div
            style={{
              maxHeight: 400,
              overflowY: 'auto',
              background: '#f5f5f5',
              padding: 12,
              borderRadius: 4,
              fontFamily: 'monospace',
              fontSize: 12,
              whiteSpace: 'pre-wrap',
              wordBreak: 'break-all',
              marginTop: 8,
            }}
          >
            {rssXmlContent || '加载中...'}
          </div>
        </div>
      </Modal>

      {/* 阶段编辑弹窗 */}
      <Modal
        title="设置写作阶段"
        open={stageModalVisible}
        onOk={handleSaveStage}
        onCancel={() => setStageModalVisible(false)}
        okText="保存"
        cancelText="取消"
      >
        <div style={{ padding: '16px 0' }}>
          <Text>请选择该文案所属的写作阶段：</Text>
          <div style={{ marginTop: 16 }}>
            <Select
              style={{ width: '100%' }}
              placeholder="选择阶段"
              value={selectedStage}
              onChange={setSelectedStage}
              size="large"
            >
              <Option value="shenti">审题分析 - 如何分析作文题目</Option>
              <Option value="gousi">构思提纲 - 如何构建文章框架</Option>
              <Option value="xiezuo">写作辅助 - 范文和写作技巧</Option>
              <Option value="pinggu">写作评估 - 作文批改和优化建议</Option>
            </Select>
          </div>
          <div style={{ marginTop: 16, padding: 12, background: '#f5f5f5', borderRadius: 4 }}>
            <Text type="secondary" style={{ fontSize: 12 }}>
              说明：每个阶段对应一个独立的RSS Feed，方便用户根据需要订阅特定阶段的播客内容。
            </Text>
          </div>
        </div>
      </Modal>

      {/* 音频关联弹窗 */}
      <Modal
        title="关联播客音频"
        open={audioModalVisible}
        onOk={handleSaveAudioAssociation}
        onCancel={() => setAudioModalVisible(false)}
        okText="保存关联"
        cancelText="取消"
        width={600}
      >
        <div style={{ padding: '16px 0' }}>
          <Text>选择要关联的音频文件（可多选）：</Text>
          <div style={{ marginTop: 16 }}>
            {audioFileList.length === 0 ? (
              <Alert
                message="暂无音频文件"
                description="请先生成 TTS 语音，音频文件将自动保存在 data/podcast_audio/ 目录"
                type="info"
                showIcon
              />
            ) : (
              <List
                size="small"
                dataSource={audioFileList}
                renderItem={(file) => (
                  <List.Item
                    onClick={() => {
                      setSelectedAudioIds(prev => 
                        prev.includes(file.filename)
                          ? prev.filter(id => id !== file.filename)
                          : [...prev, file.filename]
                      );
                    }}
                    style={{
                      cursor: 'pointer',
                      background: selectedAudioIds.includes(file.filename) ? '#e6f4ff' : 'transparent',
                      borderRadius: 4,
                      padding: '8px 12px',
                    }}
                  >
                    <List.Item.Meta
                      avatar={
                        <input
                          type="checkbox"
                          checked={selectedAudioIds.includes(file.filename)}
                          readOnly
                        />
                      }
                      title={file.filename}
                      description={`${file.size_mb} MB · ${file.created_at}`}
                    />
                  </List.Item>
                )}
              />
            )}
          </div>
        </div>
      </Modal>
    </div>
  );
};

export default PodcastPage;
