import React, { useState, useEffect } from 'react';
import { Table, Button, Tag, Typography, Card, message } from 'antd';
import {
  ClockCircleOutlined,
  DeleteOutlined,
  ThunderboltOutlined,
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import { useNavigate } from 'react-router-dom';
import { practiceApi } from '../../api/practice';
import type { PracticeSessionSummary } from '../../types/practice';

const { Title, Text } = Typography;

const formatTime = (seconds: number) => {
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  if (m >= 60) {
    const h = Math.floor(m / 60);
    return `${h}时${m % 60}分`;
  }
  return `${m}分${s}秒`;
};

const statusMap: Record<string, { color: string; label: string }> = {
  completed: { color: 'success', label: '已完成' },
  in_progress: { color: 'processing', label: '进行中' },
  abandoned: { color: 'default', label: '已放弃' },
};

const History: React.FC = () => {
  const navigate = useNavigate();
  const [sessions, setSessions] = useState<PracticeSessionSummary[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [loading, setLoading] = useState(false);

  const fetchData = async (p = page, ps = pageSize) => {
    setLoading(true);
    try {
      const res = await practiceApi.history(p, ps);
      setSessions(res.sessions || []);
      setTotal(res.total || 0);
    } catch {
      // handled
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [page, pageSize]);

  const handleDelete = async (id: string) => {
    try {
      await practiceApi.deleteSession(id);
      message.success('已删除');
      fetchData();
    } catch {
      // handled
    }
  };

  const columns: ColumnsType<PracticeSessionSummary> = [
    {
      title: '题目',
      dataIndex: 'topic',
      key: 'topic',
      ellipsis: true,
      width: 240,
      render: (text: string) => <Text strong>{text}</Text>,
    },
    {
      title: '开始时间',
      dataIndex: 'started_at',
      key: 'started_at',
      width: 160,
      render: (val: string) => val ? new Date(val).toLocaleString('zh-CN') : '-',
    },
    {
      title: '总用时',
      dataIndex: 'total_time_seconds',
      key: 'total_time',
      width: 100,
      render: (val: number) => (
        <Tag icon={<ClockCircleOutlined />}>{formatTime(val || 0)}</Tag>
      ),
    },
    {
      title: '总分',
      dataIndex: 'total_score',
      key: 'total_score',
      width: 80,
      render: (val: number | null) => val !== null ? (
        <Text strong style={{ color: val >= 50 ? '#52c41a' : '#ff4d4f', fontSize: 16 }}>
          {val}
        </Text>
      ) : <Text type="secondary">-</Text>,
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 90,
      render: (val: string) => {
        const s = statusMap[val] || { color: 'default', label: val };
        return <Tag color={s.color}>{s.label}</Tag>;
      },
    },
    {
      title: '操作',
      key: 'actions',
      width: 100,
      render: (_: unknown, record: PracticeSessionSummary) => (
        <Button
          type="text"
          danger
          size="small"
          icon={<DeleteOutlined />}
          onClick={() => handleDelete(record.id)}
        >
          删除
        </Button>
      ),
    },
  ];

  return (
    <div className="page-container">
      <Card>
        <div style={{ marginBottom: 16, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div>
            <Title level={4} style={{ margin: 0 }}>
              <ThunderboltOutlined style={{ marginRight: 8 }} />
              训练记录
            </Title>
            <Text type="secondary">共 {total} 次训练</Text>
          </div>
          <Button type="primary" onClick={() => navigate('/practice')}>
            开始新训练
          </Button>
        </div>

        <Table<PracticeSessionSummary>
          rowKey="id"
          columns={columns}
          dataSource={sessions}
          loading={loading}
          pagination={{
            current: page,
            pageSize,
            total,
            showSizeChanger: true,
            pageSizeOptions: ['10', '20', '50'],
            onChange: (p, ps) => {
              setPage(p);
              setPageSize(ps);
            },
            showTotal: (t) => `共 ${t} 条`,
          }}
          locale={{ emptyText: '暂无训练记录，点击上方按钮开始第一次训练' }}
        />
      </Card>
    </div>
  );
};

export default History;
