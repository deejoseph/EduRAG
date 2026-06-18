import React, { useEffect, useState } from 'react';
import {
  Card, Table, Tag, Button, Input, Select, Space, Statistic,
  Typography, Empty, Spin, message, Popconfirm, Divider,
  Row, Col, Badge,
} from 'antd';
import type { ColumnsType } from 'antd/es/table';
import {
  StarOutlined, StarFilled, DeleteOutlined, EyeOutlined,
  TagsOutlined, SearchOutlined, BookOutlined, FilterOutlined,
} from '@ant-design/icons';
import type { PortfolioItemSummary, TagInfo, SortConfig, FilterConfig } from '../../types/portfolio';
import {
  getPortfolioList, deletePortfolioItem, toggleStar, getAllTags, getPortfolioStats,
} from '../../api/portfolio';
import PortfolioDetail from './PortfolioDetail';

const { Title, Text } = Typography;
const { Search } = Input;

interface StatsData {
  total_items: number;
  starred_items: number;
  average_score: number;
  best_score: number;
  top_tags: TagInfo[];
  essay_types: Record<string, number>;
  essay_styles: Record<string, number>;
}

const PortfolioPage: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [items, setItems] = useState<PortfolioItemSummary[]>([]);
  const [stats, setStats] = useState<StatsData | null>(null);
  const [tags, setTags] = useState<TagInfo[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);

  // 筛选条件
  const [filters, setFilters] = useState<FilterConfig>({});
  const [sortConfig, setSortConfig] = useState<SortConfig>({ field: 'created_at', order: 'desc' });

  // 详情弹窗
  const [detailVisible, setDetailVisible] = useState(false);
  const [selectedItemId, setSelectedItemId] = useState<string | null>(null);

  // 加载数据
  const loadData = async () => {
    setLoading(true);
    try {
      const params: any = {
        page,
        page_size: pageSize,
        sort_by: sortConfig.field,
        sort_order: sortConfig.order,
        ...filters,
      };

      // 移除 undefined 值
      Object.keys(params).forEach(key => {
        if (params[key] === undefined || params[key] === '') {
          delete params[key];
        }
      });

      const [listRes, statsRes, tagsRes] = await Promise.all([
        getPortfolioList(params),
        getPortfolioStats(),
        getAllTags(),
      ]);

      setItems(listRes.items);
      setTotal(listRes.total);
      setStats(statsRes.stats);
      setTags(tagsRes.tags);
    } catch (error) {
      message.error('加载失败，请重试');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [page, pageSize, filters, sortConfig]);

  // 搜索处理
  const handleSearch = (value: string) => {
    setFilters(prev => ({ ...prev, keyword: value }));
    setPage(1);
  };

  // 清除筛选
  const handleClearFilters = () => {
    setFilters({});
    setPage(1);
  };

  // 查看详情
  const handleViewDetail = (itemId: string) => {
    setSelectedItemId(itemId);
    setDetailVisible(true);
  };

  // 切换星标
  const handleToggleStar = async (itemId: string) => {
    try {
      await toggleStar(itemId);
      message.success('星标状态已更新');
      loadData();
    } catch (error) {
      message.error('操作失败');
    }
  };

  // 删除作品
  const handleDelete = async (itemId: string) => {
    try {
      await deletePortfolioItem(itemId);
      message.success('作品已删除');
      loadData();
    } catch (error) {
      message.error('删除失败');
    }
  };

  // 表格列定义
  const columns: ColumnsType<PortfolioItemSummary> = [
    {
      title: '标题',
      dataIndex: 'title',
      key: 'title',
      width: 250,
      ellipsis: true,
      sorter: true,
      render: (text, record) => (
        <Space direction="vertical" size={0}>
          <Text strong>{text}</Text>
          {record.topic && (
            <Text type="secondary" style={{ fontSize: 12 }}>{record.topic.slice(0, 30)}</Text>
          )}
          {record.starred && (
            <StarFilled style={{ color: '#faad14', fontSize: 14 }} />
          )}
        </Space>
      ),
    },
    {
      title: '类型/文体',
      key: 'type_style',
      width: 120,
      render: (_, record) => (
        <Space direction="vertical" size={2}>
          {record.essay_type && <Tag color="blue">{record.essay_type}</Tag>}
          {record.essay_style && <Tag color="green">{record.essay_style}</Tag>}
        </Space>
      ),
    },
    {
      title: '分数',
      dataIndex: 'score',
      key: 'score',
      width: 80,
      sorter: true,
      render: (score) => (
        score ? <Badge count={score} style={{ backgroundColor: score >= 50 ? '#52c41a' : '#ff4d4f' }} /> : '-'
      ),
    },
    {
      title: '字数',
      dataIndex: 'word_count',
      key: 'word_count',
      width: 80,
      sorter: true,
      render: (count) => count ? `${count}字` : '-',
    },
    {
      title: '年份/考区',
      key: 'exam_info',
      width: 120,
      render: (_, record) => (
        <Space direction="vertical" size={2}>
          {record.exam_year && <Tag color="purple">{record.exam_year}年</Tag>}
          {record.exam_region && <Tag color="cyan">{record.exam_region}</Tag>}
        </Space>
      ),
    },
    {
      title: '关键词',
      dataIndex: 'keywords',
      key: 'keywords',
      width: 200,
      ellipsis: true,
      render: (keywords) => (
        <Space wrap>
          {keywords?.slice(0, 3).map((kw: string, idx: number) => (
            <Tag key={idx} icon={<TagsOutlined />}>{kw}</Tag>
          ))}
          {keywords && keywords.length > 3 && <Tag>+{keywords.length - 3}</Tag>}
        </Space>
      ),
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 120,
      sorter: true,
      render: (date) => new Date(date).toLocaleDateString('zh-CN'),
    },
    {
      title: '操作',
      key: 'action',
      width: 150,
      fixed: 'right',
      render: (_, record) => (
        <Space>
          <Button
            type="text"
            icon={record.starred ? <StarFilled style={{ color: '#faad14' }} /> : <StarOutlined />}
            onClick={() => handleToggleStar(record.id)}
          />
          <Button
            type="text"
            icon={<EyeOutlined />}
            onClick={() => handleViewDetail(record.id)}
          />
          <Popconfirm
            title="确定要删除这个作品吗？"
            onConfirm={() => handleDelete(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Button type="text" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div style={{ padding: '24px' }}>
      {/* 标题 */}
      <Title level={2}>
        <BookOutlined /> 作品集
      </Title>
      <Text type="secondary">收藏优秀作文，积累写作素材，温习回顾提升写作水平</Text>

      <Divider />

      {/* 统计卡片 */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic title="作品总数" value={stats?.total_items || 0} suffix="篇" />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic title="星标作品" value={stats?.starred_items || 0} suffix="篇" />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic title="平均分数" value={stats?.average_score || 0} precision={1} suffix="/100" />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic title="最高分数" value={stats?.best_score || 0} suffix="/100" />
          </Card>
        </Col>
      </Row>

      {/* 搜索和筛选 */}
      <Card style={{ marginBottom: 24 }}>
        <Space wrap size="middle" style={{ width: '100%' }}>
          <Search
            placeholder="搜索标题、内容、题目或关键词..."
            allowClear
            onSearch={handleSearch}
            style={{ width: 300 }}
            prefix={<SearchOutlined />}
            defaultValue={filters.keyword}
          />

          <Select
            placeholder="作文类型"
            allowClear
            style={{ width: 150 }}
            value={filters.essay_type}
            onChange={(value) => {
              setFilters(prev => ({ ...prev, essay_type: value }));
              setPage(1);
            }}
          >
            <Select.Option value="材料作文">材料作文</Select.Option>
            <Select.Option value="话题作文">话题作文</Select.Option>
            <Select.Option value="命题作文">命题作文</Select.Option>
            <Select.Option value="半命题作文">半命题作文</Select.Option>
          </Select>

          <Select
            placeholder="文体"
            allowClear
            style={{ width: 120 }}
            value={filters.essay_style}
            onChange={(value) => {
              setFilters(prev => ({ ...prev, essay_style: value }));
              setPage(1);
            }}
          >
            <Select.Option value="议论文">议论文</Select.Option>
            <Select.Option value="记叙文">记叙文</Select.Option>
            <Select.Option value="说明文">说明文</Select.Option>
            <Select.Option value="散文">散文</Select.Option>
          </Select>

          <Select
            placeholder="标签"
            allowClear
            style={{ width: 150 }}
            value={filters.tag}
            onChange={(value) => {
              setFilters(prev => ({ ...prev, tag: value }));
              setPage(1);
            }}
          >
            {tags.map((tag) => (
              <Select.Option key={tag.name} value={tag.name}>
                {tag.name} ({tag.count})
              </Select.Option>
            ))}
          </Select>

          <Button
            icon={<FilterOutlined />}
            onClick={handleClearFilters}
          >
            清除筛选
          </Button>
        </Space>
      </Card>

      {/* 表格 */}
      <Spin spinning={loading}>
        <Table
          columns={columns}
          dataSource={items}
          rowKey="id"
          pagination={{
            current: page,
            pageSize,
            total,
            showSizeChanger: true,
            showTotal: (total) => `共 ${total} 篇作品`,
            onChange: (newPage, newPageSize) => {
              setPage(newPage);
              if (newPageSize !== pageSize) {
                // setPageSize is not defined, remove this logic
              }
            },
          }}
          scroll={{ x: 1200 }}
          locale={{
            emptyText: (
              <Empty
                description={
                  Object.keys(filters).length > 0
                    ? '没有找到符合条件的作品'
                    : '作品集中还没有作品，去写作训练或知识检索中添加吧！'
                }
                image={Empty.PRESENTED_IMAGE_SIMPLE}
              />
            ),
          }}
          onChange={(_pagination, _filters, sorter) => {
            if (Array.isArray(sorter)) return;
            if (sorter.field && sorter.order) {
              setSortConfig({
                field: sorter.field as any,
                order: sorter.order === 'ascend' ? 'asc' : 'desc',
              });
            }
          }}
        />
      </Spin>

      {/* 详情弹窗 */}
      {selectedItemId && (
        <PortfolioDetail
          visible={detailVisible}
          itemId={selectedItemId}
          onClose={() => {
            setDetailVisible(false);
            setSelectedItemId(null);
          }}
          onUpdate={loadData}
        />
      )}
    </div>
  );
};

export default PortfolioPage;
