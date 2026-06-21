/**
 * 播客模块主页面
 * 展示从写作训练各阶段导入的素材，支持查看、编辑和管理
 */

import React, { useState, useEffect } from 'react';
import { Card, Table, Tag, Button, Space, Typography, Empty, Modal, message, Badge, Input, Select } from 'antd';
import { SoundOutlined, EyeOutlined, DeleteOutlined, DownloadOutlined, StarOutlined } from '@ant-design/icons';
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
    </div>
  );
};

export default PodcastPage;
