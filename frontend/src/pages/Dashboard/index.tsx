import React, { useEffect, useState } from 'react';
import { Card, Row, Col, Statistic, Button, Table, Tag, Alert } from 'antd';
import {
  DatabaseOutlined,
  EditOutlined,
  SearchOutlined,
  ApiOutlined,
  ThunderboltOutlined,
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { healthApi, searchApi } from '../../api/search';
import type { StatsResponse, CollectionsResponse, HealthResponse } from '../../types/api';

const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [stats, setStats] = useState<StatsResponse | null>(null);
  const [collections, setCollections] = useState<CollectionsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const [h, s, c] = await Promise.all([
          healthApi.check(),
          searchApi.stats(),
          searchApi.collections(),
        ]);
        setHealth(h);
        setStats(s);
        setCollections(c);
      } catch (e: any) {
        setError('无法连接后端服务，请确认后端已启动');
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const collectionColumns = [
    { title: '集合名称', dataIndex: 'name', key: 'name' },
    {
      title: '文档数',
      dataIndex: 'count',
      key: 'count',
      render: (count: number) => <Tag color="blue">{count.toLocaleString()}</Tag>,
    },
  ];

  if (error) {
    return (
      <div className="page-container">
        <Alert
          message="连接失败"
          description={error}
          type="error"
          showIcon
          action={<Button size="small" onClick={() => window.location.reload()}>重试</Button>}
        />
      </div>
    );
  }

  return (
    <div className="page-container">
      <h2 style={{ marginBottom: 24 }}>EduRAG 智能写作助手</h2>

      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} lg={6}>
          <Card loading={loading}>
            <Statistic
              title="后端状态"
              value={health?.status === 'ok' ? '正常运行' : '未知'}
              prefix={<ApiOutlined style={{ color: '#52c41a' }} />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card loading={loading}>
            <Statistic
              title="知识库文档"
              value={stats?.total_documents || 0}
              prefix={<DatabaseOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card loading={loading}>
            <Statistic
              title="LLM 模型"
              value={stats?.llm_model || '-'}
              prefix={<ThunderboltOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card loading={loading}>
            <Statistic
              title="数据集合"
              value={stats?.total_collections || 0}
              prefix={<DatabaseOutlined />}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: 24 }}>
        <Col xs={24} sm={12}>
          <Card>
            <Button
              type="primary"
              icon={<EditOutlined />}
              size="large"
              block
              onClick={() => navigate('/writing')}
            >
              开始写作训练
            </Button>
            <p style={{ marginTop: 8, color: '#666', textAlign: 'center' }}>
              审题 → 构思 → 写作辅助 → 作文评估
            </p>
          </Card>
        </Col>
        <Col xs={24} sm={12}>
          <Card>
            <Button
              icon={<SearchOutlined />}
              size="large"
              block
              onClick={() => navigate('/search')}
            >
              知识库检索
            </Button>
            <p style={{ marginTop: 8, color: '#666', textAlign: 'center' }}>
              搜索范文、素材、真题
            </p>
          </Card>
        </Col>
      </Row>

      <Card title="数据集合" style={{ marginTop: 24 }} loading={loading}>
        <Table
          dataSource={collections?.collections || []}
          columns={collectionColumns}
          rowKey="name"
          pagination={false}
          size="small"
        />
      </Card>
    </div>
  );
};

export default Dashboard;
