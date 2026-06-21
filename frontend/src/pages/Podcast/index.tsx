/**
 * 播客模块主页面
 * 展示从写作训练各阶段导入的素材，支持查看、编辑和管理
 */

import React, { useState, useEffect } from 'react';
import { Card, Table, Tag, Button, Space, Typography, Empty, Modal, message, Badge, Input, Select, Upload, Progress, Divider } from 'antd';
import { SoundOutlined, EyeOutlined, DeleteOutlined, DownloadOutlined, StarOutlined, PlayCircleOutlined, PauseCircleOutlined, CloudUploadOutlined } from '@ant-design/icons';
import { writingApi } from '../../api/writing';
import type { PodcastMaterial } from '../../api/writing';

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
  const [prompt, setPrompt] = useState('请将这些素材整理成一段播客对话，风格轻松有趣');
  const [selectedModel, setSelectedModel] = useState('qwen3:8b');
  
  // TTS语音生成相关状态
  const [ttsModalVisible, setTtsModalVisible] = useState(false);
  const [ttsGenerating, setTtsGenerating] = useState(false);
  const [refAudioFile, setRefAudioFile] = useState<File | null>(null);
  const [promptText, setPromptText] = useState('这是一段播客对话');
  const [ttsMode, setTtsMode] = useState<'precise' | 'standard' | 'fast'>('standard');
  const [nfe, setNfe] = useState(18);
  const [guidanceStrength, setGuidanceStrength] = useState(3.5);
  const [audioSegments, setAudioSegments] = useState<Array<{text: string; audio_url?: string; duration?: number; status: 'pending' | 'generating' | 'completed' | 'failed'}>>([]);
  const [currentPlayingIndex, setCurrentPlayingIndex] = useState<number | null>(null);
  const [audioPlayer, setAudioPlayer] = useState<HTMLAudioElement | null>(null);

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

  useEffect(() => {
    loadMaterials();
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
      
      // 刷新素材列表（更新状态）
      loadMaterials();
    } catch (error) {
      console.error('生成播客文案失败:', error);
      message.error('生成播客文案失败');
    } finally {
      setGenerating(false);
    }
  };

  // 打开TTS语音生成弹窗
  const handleOpenTtsModal = () => {
    if (!generatedScript) {
      message.warning('请先生成播客文案');
      return;
    }
    
    // 智能分段文案
    const segments = splitScriptIntoSegments(generatedScript);
    setAudioSegments(segments.map(text => ({
      text,
      status: 'pending' as const
    })));
    setTtsModalVisible(true);
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
    if (!refAudioFile) {
      message.warning('请先上传参考音频');
      return;
    }
    
    const segment = audioSegments[index];
    
    // 更新状态为生成中
    const updatedSegments = [...audioSegments];
    updatedSegments[index] = { ...segment, status: 'generating' };
    setAudioSegments(updatedSegments);
    
    try {
      console.log('开始调用TTS API...');
      // 直接调用API
      const response = await writingApi.generatePodcastTTS({
        text: segment.text,
        ref_audio: refAudioFile,
        prompt_text: promptText,  // 使用用户输入的提示文本
        nfe,
        guidance_strength: guidanceStrength,
      });
      
      console.log('TTS响应:', response);
      console.log('音频URL:', response.audio_url);
      console.log('时长:', response.duration_sec);
      
      // 更新状态为完成
      updatedSegments[index] = {
        ...segment,
        audio_url: response.audio_url,
        duration: response.duration_sec,
        status: 'completed'
      };
      console.log('更新后的segments:', updatedSegments[index]);
      setAudioSegments(updatedSegments);
      message.success(`第 ${index + 1} 段语音生成成功！`);
    } catch (error: any) {
      console.error('生成语音失败:', error);
      console.error('错误详情:', error.response || error.message);
      updatedSegments[index] = { ...segment, status: 'failed' };
      setAudioSegments(updatedSegments);
      message.error(`第 ${index + 1} 段语音生成失败: ${error.message || '未知错误'}`);
    }
  };

  // 批量生成所有段落的语音
  const handleGenerateAllAudio = async () => {
    if (!refAudioFile) {
      message.warning('请先上传参考音频');
      return;
    }
    
    setTtsGenerating(true);
    
    try {
      // 逐段生成
      for (let i = 0; i < audioSegments.length; i++) {
        if (audioSegments[i].status === 'pending' || audioSegments[i].status === 'failed') {
          await handleGenerateSegmentAudio(i);
        }
      }
      
      message.success('所有段落语音生成完成！');
    } catch (error) {
      console.error('批量生成失败:', error);
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

  // 下载完整音频（拼接所有段落）
  const handleDownloadFullAudio = () => {
    const completedSegments = audioSegments.filter(s => s.status === 'completed' && s.audio_url);
    
    if (completedSegments.length === 0) {
      message.warning('没有可下载的音频');
      return;
    }
    
    // 下载第一个音频作为示例（完整拼接需要后端支持）
    const firstAudio = completedSegments[0].audio_url!;
    const link = document.createElement('a');
    link.href = firstAudio;
    link.download = `podcast_${new Date().getTime()}.wav`;
    link.click();
    message.success('开始下载');
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
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
      render: (time: string) => new Date(time).toLocaleString('zh-CN'),
    },
    {
      title: '操作',
      key: 'action',
      width: 200,
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
            <SoundOutlined /> 播客素材管理
          </Title>
          <Text type="secondary">
            这里展示了从写作训练各阶段导入的素材，您可以查看、导出或删除这些素材。
          </Text>
        </div>

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
            <div style={{ marginBottom: 16 }}>
              <Badge count="成功" style={{ backgroundColor: '#52c41a' }} />
              <Text strong style={{ marginLeft: 8 }}>播客文案已生成！</Text>
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
          setTtsModalVisible(false);
          setRefAudioFile(null);
          setAudioSegments([]);
          setCurrentPlayingIndex(null);
        }}
        footer={[
          <Button key="close" onClick={() => {
            setTtsModalVisible(false);
            setRefAudioFile(null);
            setAudioSegments([]);
            setCurrentPlayingIndex(null);
          }}>
            关闭
          </Button>,
          <Button
            key="generate-all"
            type="primary"
            icon={<CloudUploadOutlined />}
            onClick={handleGenerateAllAudio}
            loading={ttsGenerating}
            disabled={!refAudioFile || audioSegments.length === 0}
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
                    setRefAudioFile(file);
                    message.success(`已选择: ${file.name}`);
                    return false; // 阻止自动上传
                  }}
                  onRemove={() => setRefAudioFile(null)}
                >
                  <Button icon={<CloudUploadOutlined />}>
                    选择音频文件
                  </Button>
                </Upload>
                {refAudioFile && (
                  <Text type="success" style={{ marginTop: 8, display: 'block' }}>
                    ✓ 已选择: {refAudioFile.name} ({(refAudioFile.size / 1024).toFixed(1)} KB)
                  </Text>
                )}
              </div>

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
                    <Text type="secondary" style={{ fontSize: 12, marginLeft: 4 }}>(10-30，默认18)</Text>
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
                    <Text type="secondary" style={{ fontSize: 12, marginLeft: 4 }}>(2.0-5.0，默认3.5)</Text>
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
                          disabled={!refAudioFile || segment.status === 'generating'}
                          loading={segment.status === 'generating'}
                        >
                          {segment.status === 'completed' ? '重新生成' : '生成语音'}
                        </Button>

                        {segment.status === 'completed' && segment.audio_url && (
                          <Button
                            size="small"
                            icon={currentPlayingIndex === index ? <PauseCircleOutlined /> : <PlayCircleOutlined />}
                            onClick={() => handlePlayAudio(index, segment.audio_url!)}
                          >
                            {currentPlayingIndex === index ? '暂停' : '试听'}
                          </Button>
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
            </div>
          )}
        </div>
      </Modal>
    </div>
  );
};

export default PodcastPage;
