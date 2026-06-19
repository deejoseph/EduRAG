import React, { useEffect, useState } from 'react';
import { Card, Descriptions, Tag, Button, Alert, Spin, Space, Divider, Typography, Popconfirm, message, Select } from 'antd';
import {
  CheckCircleOutlined, CloseCircleOutlined,
  ThunderboltOutlined, DatabaseOutlined, ReloadOutlined,
  DeleteOutlined, LineChartOutlined, SwapOutlined,
} from '@ant-design/icons';
import { healthApi, searchApi } from '../../api/search';
import { resetPortfolio } from '../../api/portfolio';
import { practiceApi } from '../../api/practice';
import type { HealthResponse, StatsResponse } from '../../types/api';

const { Text, Title } = Typography;

const Settings: React.FC = () => {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [stats, setStats] = useState<StatsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // 模型切换相关状态
  const [currentModel, setCurrentModel] = useState<string>('');
  const [availableModels, setAvailableModels] = useState<Array<{value: string; label: string}>>([]);
  const [modelLoading, setModelLoading] = useState(false);
  const [switchingModel, setSwitchingModel] = useState(false);

  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [h, s] = await Promise.all([
        healthApi.check(),
        searchApi.stats(),
      ]);
      setHealth(h);
      setStats(s);
    } catch {
      setError('无法连接后端服务，请确认后端已启动（python -m api.app）');
    } finally {
      setLoading(false);
    }
  };

  // 获取模型信息
  const fetchModelInfo = async () => {
    try {
      setModelLoading(true);
      const res = await healthApi.getModel();
      console.log('[Settings] 模型API响应:', res);
      console.log('[Settings] 当前模型:', res.model);
      console.log('[Settings] 可用模型列表:', res.available_models);
      setCurrentModel(res.model);
      setAvailableModels(res.available_models);
    } catch (err) {
      console.error('获取模型信息失败:', err);
    } finally {
      setModelLoading(false);
    }
  };

  // 切换模型
  const handleSwitchModel = async (newModel: string) => {
    if (newModel === currentModel) return;

    try {
      setSwitchingModel(true);
      const res = await healthApi.setModel(newModel);
      message.success(res.message || '模型切换成功');
      setCurrentModel(newModel);
      // 刷新页面数据以更新模型显示
      await fetchData();
    } catch (err: any) {
      message.error(err.message || '模型切换失败');
    } finally {
      setSwitchingModel(false);
    }
  };

  useEffect(() => {
    fetchData();
    fetchModelInfo();
  }, []);

  // 重置作品集
  const handleResetPortfolio = async () => {
    try {
      const res = await resetPortfolio();
      message.success(`已删除 ${res.deleted} 篇作品`);
      fetchData();
    } catch (error) {
      message.error('重置失败');
    }
  };

  // 重置成长日志
  const handleResetGrowthLog = async () => {
    try {
      const res = await practiceApi.resetLog();
      message.success(`已删除 ${res.deleted} 条训练记录`);
      fetchData();
    } catch (error) {
      message.error('重置失败');
    }
  };

  return (
    <div className="page-container">
      <Space style={{ marginBottom: 24, width: '100%', justifyContent: 'space-between' }}>
        <Title level={4} style={{ margin: 0 }}>系统设置</Title>
        <Button icon={<ReloadOutlined />} onClick={fetchData} loading={loading}>
          刷新状态
        </Button>
      </Space>

      {error && (
        <Alert
          message="连接失败"
          description={error}
          type="error"
          showIcon
          style={{ marginBottom: 24 }}
          action={<Button size="small" onClick={fetchData}>重试</Button>}
        />
      )}

      <Spin spinning={loading}>
        {/* 后端连接状态 */}
        <Card title="后端服务" style={{ marginBottom: 16 }}>
          <Descriptions column={{ xs: 1, sm: 2 }}>
            <Descriptions.Item label="连接状态">
              {health?.status === 'ok' ? (
                <Tag icon={<CheckCircleOutlined />} color="success">正常</Tag>
              ) : (
                <Tag icon={<CloseCircleOutlined />} color="error">未连接</Tag>
              )}
            </Descriptions.Item>
            <Descriptions.Item label="API 地址">
              <Text code>/api-proxy</Text>
              <Text type="secondary" style={{ marginLeft: 8 }}>→ localhost:5000</Text>
            </Descriptions.Item>
            <Descriptions.Item label="最后检查">
              {health?.timestamp || '-'}
            </Descriptions.Item>
          </Descriptions>
        </Card>

        {/* 模型信息 */}
        <Card title="模型配置" style={{ marginBottom: 16 }}>
          <Descriptions column={{ xs: 1, sm: 2 }}>
            <Descriptions.Item label="LLM 模型">
              <Space>
                <ThunderboltOutlined style={{ color: '#1890ff' }} />
                <Text>{stats?.llm_model || health?.model || currentModel || '-'}</Text>
              </Space>
            </Descriptions.Item>
            <Descriptions.Item label="Embedding 模型">
              <Space>
                <DatabaseOutlined style={{ color: '#52c41a' }} />
                <Text>{stats?.embedding_model || health?.embedding_model || '-'}</Text>
              </Space>
            </Descriptions.Item>
          </Descriptions>

          <Divider style={{ margin: '16px 0 12px 0' }} />

          <Spin spinning={modelLoading}>
            <Space direction="vertical" style={{ width: '100%' }}>
              <Text strong>切换模型：</Text>
              <Select
                value={currentModel}
                onChange={handleSwitchModel}
                loading={switchingModel}
                disabled={switchingModel}
                style={{ width: 300 }}
                options={availableModels}
                suffixIcon={<SwapOutlined />}
              />
              {switchingModel && (
                <Text type="secondary" style={{ fontSize: 12 }}>
                  正在切换模型，请稍候...
                </Text>
              )}
            </Space>
          </Spin>
        </Card>

        {/* 知识库统计 */}
        <Card title="知识库统计" style={{ marginBottom: 16 }}>
          <Descriptions column={{ xs: 1, sm: 2, md: 3 }}>
            <Descriptions.Item label="数据集合">
              <Tag color="blue">{stats?.total_collections || 0} 个</Tag>
            </Descriptions.Item>
            <Descriptions.Item label="文档总数">
              <Tag color="green">{(stats?.total_documents || 0).toLocaleString()} 条</Tag>
            </Descriptions.Item>
          </Descriptions>
          {stats?.collections && stats.collections.length > 0 && (
            <>
              <Divider style={{ margin: '12px 0' }} />
              <Space wrap>
                {stats.collections.map(col => (
                  <Tag key={col.name} color="processing">
                    {col.name}: {col.count.toLocaleString()}
                  </Tag>
                ))}
              </Space>
            </>
          )}
        </Card>

        {/* 关于 */}
        <Card title="关于" style={{ marginBottom: 16 }}>
          <Descriptions column={1}>
            <Descriptions.Item label="应用名称">EduRAG 智能学习助手</Descriptions.Item>
            <Descriptions.Item label="版本">1.0.0</Descriptions.Item>
            <Descriptions.Item label="适用场景">高考语文作文训练</Descriptions.Item>
            <Descriptions.Item label="功能">
              审题分析 → 构思提纲 → 引导练习 → 作文评估
            </Descriptions.Item>
          </Descriptions>
        </Card>

        {/* 数据管理 */}
        <Card title="数据管理">
          <Space direction="vertical" style={{ width: '100%' }}>
            <Alert
              message="注意"
              description="以下操作将永久删除数据，不可恢复。请谨慎操作。"
              type="warning"
              showIcon
            />
            <Space wrap>
              <Popconfirm
                title="确定要清空作品集吗？"
                description="这将删除所有收藏的作文作品，此操作不可恢复。"
                onConfirm={handleResetPortfolio}
                okText="确定删除"
                cancelText="取消"
              >
                <Button danger icon={<DeleteOutlined />}>
                  清空作品集
                </Button>
              </Popconfirm>

              <Popconfirm
                title="确定要重置成长日志吗？"
                description="这将删除所有计入成长日志的训练记录，此操作不可恢复。"
                onConfirm={handleResetGrowthLog}
                okText="确定删除"
                cancelText="取消"
              >
                <Button danger icon={<LineChartOutlined />}>
                  重置成长日志
                </Button>
              </Popconfirm>
            </Space>
          </Space>
        </Card>
      </Spin>
    </div>
  );
};

export default Settings;
