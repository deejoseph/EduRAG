import React, { useEffect, useState } from 'react';
import { Card, Descriptions, Tag, Button, Alert, Spin, Space, Divider, Typography, Popconfirm, message, Select } from 'antd';
import {
  CheckCircleOutlined, CloseCircleOutlined,
  ThunderboltOutlined, DatabaseOutlined, ReloadOutlined,
  DeleteOutlined, LineChartOutlined, SwapOutlined,
  DownloadOutlined,
} from '@ant-design/icons';
import { healthApi, searchApi } from '../../api/search';
import { resetPortfolio } from '../../api/portfolio';
import { practiceApi } from '../../api/practice';
import { backupDatabase, listBackups, deleteBackup, restoreBackup, exportConversation } from '../../api/backup';
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

  // 备份相关状态
  const [backups, setBackups] = useState<Array<{name: string; size_mb: number; created_at: string; collections?: Array<{name: string; document_count: number}>; total_collections?: number}>>([]);
  const [loadingBackups, setLoadingBackups] = useState(false);
  const [backingUp, setBackingUp] = useState(false);
  const [exporting, setExporting] = useState(false);

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
    loadBackups();  // 新增：加载备份列表
  }, []);

  // 加载备份列表
  const loadBackups = async () => {
    try {
      setLoadingBackups(true);
      const res = await listBackups();
      setBackups(res.backups.slice(0, 5)); // 只显示最近5个
    } catch (error) {
      console.error('加载备份列表失败:', error);
    } finally {
      setLoadingBackups(false);
    }
  };

  // 备份数据库
  const handleBackupDatabase = async () => {
    try {
      setBackingUp(true);
      const res = await backupDatabase();
      message.success(`备份成功！（包含 ${res.total_collections || 0} 个知识库）大小: ${res.size_mb.toFixed(2)} MB`);
      await loadBackups(); // 刷新备份列表
    } catch (error: any) {
      const errorMsg = error?.response?.data?.error || '备份失败';
      message.error(errorMsg);
    } finally {
      setBackingUp(false);
    }
  };

  // 导出对话记录
  const handleExportConversation = async () => {
    try {
      setExporting(true);
      await exportConversation(undefined, 'markdown');
      message.success('对话记录已导出，请查看下载文件夹');
    } catch (error: any) {
      const errorMsg = error?.response?.data?.error || '导出失败';
      message.error(errorMsg);
    } finally {
      setExporting(false);
    }
  };

  // 删除备份
  const handleDeleteBackup = async (backupName: string) => {
    try {
      await deleteBackup(backupName);
      message.success('备份已删除');
      await loadBackups();
    } catch (error: any) {
      const errorMsg = error?.response?.data?.error || '删除失败';
      message.error(errorMsg);
    }
  };

  // 恢复备份
  const handleRestoreBackup = async (backupName: string) => {
    try {
      const res = await restoreBackup(backupName);
      message.warning({
        content: `${res.message}。${res.warning || ''}`,
        duration: 5,
      });
      await loadBackups();
    } catch (error: any) {
      const errorMsg = error?.response?.data?.error || '恢复失败';
      message.error(errorMsg);
    }
  };

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

        {/* 数据备份与导出 */}
        <Card title="数据备份与导出" style={{ marginTop: 16 }}>
          <Space direction="vertical" style={{ width: '100%' }} size="middle">
            {/* 备份数据库 */}
            <div>
              <Text strong>备份知识库</Text>
              <Text type="secondary" style={{ display: 'block', marginBottom: 8 }}>
                备份 ChromaDB 向量数据库到 backup 目录，保留最近5个备份
              </Text>
              <Button
                type="primary"
                icon={<DatabaseOutlined />}
                onClick={handleBackupDatabase}
                loading={backingUp}
              >
                立即备份
              </Button>
            </div>

            <Divider style={{ margin: '12px 0' }} />

            {/* 导出对话记录 */}
            <div>
              <Text strong>导出对话记录</Text>
              <Text type="secondary" style={{ display: 'block', marginBottom: 8 }}>
                导出 Qoder 对话历史为 Markdown 格式，可用于写书或归档
              </Text>
              <Button
                icon={<DownloadOutlined />}
                onClick={handleExportConversation}
                loading={exporting}
              >
                导出为 Markdown
              </Button>
            </div>

            <Divider style={{ margin: '12px 0' }} />

            {/* 备份列表 */}
            <div>
              <Text strong>历史备份</Text>
              <Spin spinning={loadingBackups}>
                {backups.length === 0 ? (
                  <Text type="secondary" style={{ display: 'block', marginTop: 8 }}>
                    暂无备份
                  </Text>
                ) : (
                  <div style={{ marginTop: 8 }}>
                    {backups.map((backup) => (
                      <div
                        key={backup.name}
                        style={{
                          display: 'flex',
                          justifyContent: 'space-between',
                          alignItems: 'center',
                          padding: '8px 12px',
                          background: '#f5f5f5',
                          borderRadius: 4,
                          marginBottom: 8,
                        }}
                      >
                        <div>
                          <Text>{backup.name}</Text>
                          <br />
                          <Text type="secondary" style={{ fontSize: 12 }}>
                            {backup.size_mb.toFixed(2)} MB · {new Date(backup.created_at).toLocaleString('zh-CN')}
                          </Text>
                          {backup.total_collections && backup.total_collections > 0 && (
                            <div style={{ marginTop: 4 }}>
                              <Text type="success" style={{ fontSize: 12 }}>
                                包含 {backup.total_collections} 个知识库：
                              </Text>
                              <Space size={4} wrap style={{ marginTop: 2 }}>
                                {backup.collections?.map((col, idx) => (
                                  <Tag key={idx} color="blue" style={{ fontSize: 11, margin: 0 }}>
                                    {col.name}: {col.document_count.toLocaleString()}
                                  </Tag>
                                ))}
                              </Space>
                            </div>
                          )}
                        </div>
                        <Space>
                          <Popconfirm
                            title="确定要从此备份恢复吗？当前数据将被自动备份。"
                            description="恢复后需要重启后端服务才能生效"
                            onConfirm={() => handleRestoreBackup(backup.name)}
                            okText="恢复"
                            cancelText="取消"
                          >
                            <Button 
                              type="primary" 
                              size="small" 
                              icon={<ReloadOutlined />}
                            >
                              恢复
                            </Button>
                          </Popconfirm>
                          <Popconfirm
                            title="确定删除此备份？"
                            onConfirm={() => handleDeleteBackup(backup.name)}
                            okText="删除"
                            cancelText="取消"
                          >
                            <Button danger size="small" icon={<DeleteOutlined />}>
                              删除
                            </Button>
                          </Popconfirm>
                        </Space>
                      </div>
                    ))}
                  </div>
                )}
              </Spin>
            </div>
          </Space>
        </Card>
      </Spin>
    </div>
  );
};

export default Settings;
