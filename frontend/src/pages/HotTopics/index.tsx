import React, { useEffect, useState } from 'react';
import {
  Card, Row, Col, Tag, Button, Select, Space, Typography, Spin,
  message, Divider, Collapse, Modal, Input, Alert, Badge, Empty,
} from 'antd';
import {
  FireOutlined, ReloadOutlined, BulbOutlined,
  SearchOutlined, StarOutlined,
} from '@ant-design/icons';
import type { TopicCategory, HotTopic } from '../../types/hotTopics';
import {
  getCategories, searchHotTopics, refreshCache, generateCustomPrompt,
} from '../../api/hotTopics';
import MarkdownRenderer from '../../components/common/MarkdownRenderer';

const { Title, Text, Paragraph } = Typography;
const { Panel } = Collapse;

const HotTopicsPage: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [categories, setCategories] = useState<TopicCategory[]>([]);
  const [topics, setTopics] = useState<HotTopic[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string | undefined>();
  const [refreshing, setRefreshing] = useState(false);

  // 自定义命题弹窗
  const [promptModalVisible, setPromptModalVisible] = useState(false);
  const [customKeywords, setCustomKeywords] = useState('');
  const [generatedPrompt, setGeneratedPrompt] = useState<string>('');
  const [generating, setGenerating] = useState(false);

  // 话题详情弹窗
  const [detailVisible, setDetailVisible] = useState(false);
  const [selectedTopic, setSelectedTopic] = useState<HotTopic | null>(null);

  // 加载分类
  useEffect(() => {
    loadCategories();
  }, []);

  const loadCategories = async () => {
    try {
      const res = await getCategories();
      setCategories(res.categories);
    } catch (error) {
      message.error('加载分类失败');
    }
  };

  // 搜索热点话题
  const handleSearch = async () => {
    setLoading(true);
    try {
      const res = await searchHotTopics({
        category_id: selectedCategory,
        use_cache: true,
      });
      setTopics(res.topics);
      if (res.topics.length === 0) {
        message.info('暂无热点数据，请点击刷新按钮生成');
      }
    } catch (error) {
      message.error('搜索失败，请重试');
    } finally {
      setLoading(false);
    }
  };

  // 刷新缓存
  const handleRefresh = async () => {
    setRefreshing(true);
    try {
      await refreshCache({
        category_id: selectedCategory,
      });
      message.success('刷新成功');
      handleSearch();
    } catch (error) {
      message.error('刷新失败');
    } finally {
      setRefreshing(false);
    }
  };

  // 生成自定义命题
  const handleGeneratePrompt = async () => {
    if (!customKeywords.trim()) {
      message.warning('请输入关键词');
      return;
    }

    setGenerating(true);
    try {
      const keywords = customKeywords.split(/[,，\s]+/).filter(k => k.trim());
      const res = await generateCustomPrompt({
        keywords,
        essay_type: '材料作文',
        difficulty: '中等',
      });
      setGeneratedPrompt(res.prompt);
    } catch (error) {
      message.error('生成失败，请重试');
    } finally {
      setGenerating(false);
    }
  };

  // 查看话题详情
  const handleViewDetail = (topic: HotTopic) => {
    setSelectedTopic(topic);
    setDetailVisible(true);
  };

  // 获取难度标签颜色
  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty) {
      case '容易': return 'green';
      case '中等': return 'orange';
      case '较难': return 'red';
      default: return 'default';
    }
  };

  return (
    <div style={{ padding: '24px' }}>
      {/* 标题 */}
      <Title level={2}>
        <FireOutlined style={{ color: '#ff4d4f' }} /> 智能命题热点
      </Title>
      <Text type="secondary">
        基于社会热点、教育动态、时政新闻，预测高考作文命题趋势
      </Text>

      <Divider />

      {/* 说明卡片 */}
      <Alert
        message="功能说明"
        description={
          <div>
            <p>本模块通过 AI 分析当前社会热点，预测可能成为高考作文题目的话题，并提供：</p>
            <ul style={{ marginBottom: 0, paddingLeft: 20 }}>
              <li>模拟高考作文题目（材料+要求）</li>
              <li>写作角度建议</li>
              <li>参考素材（名人名言、典型案例）</li>
              <li>难度评估和相关度评分</li>
            </ul>
          </div>
        }
        type="info"
        showIcon
        style={{ marginBottom: 24 }}
      />

      {/* 筛选和操作 */}
      <Card style={{ marginBottom: 24 }}>
        <Space wrap size="middle">
          <Select
            placeholder="选择分类（不选则搜索全部）"
            allowClear
            style={{ width: 200 }}
            value={selectedCategory}
            onChange={setSelectedCategory}
          >
            {categories.map((cat) => (
              <Select.Option key={cat.id} value={cat.id}>
                {cat.name}
              </Select.Option>
            ))}
          </Select>

          <Button
            type="primary"
            icon={<SearchOutlined />}
            onClick={handleSearch}
            loading={loading}
          >
            搜索热点
          </Button>

          <Button
            icon={<ReloadOutlined />}
            onClick={handleRefresh}
            loading={refreshing}
          >
            刷新缓存
          </Button>

          <Button
            icon={<BulbOutlined />}
            onClick={() => setPromptModalVisible(true)}
          >
            自定义命题
          </Button>
        </Space>
      </Card>

      {/* 热点话题列表 */}
      <Spin spinning={loading}>
        {topics.length === 0 ? (
          <Card>
            <Empty
              description="点击&quot;搜索热点&quot;按钮开始分析"
              image={Empty.PRESENTED_IMAGE_SIMPLE}
            />
          </Card>
        ) : (
          <Row gutter={[16, 16]}>
            {topics.map((topic, index) => (
              <Col xs={24} sm={12} lg={8} key={index}>
                <Card
                  hoverable
                  onClick={() => handleViewDetail(topic)}
                  extra={
                    <Badge count={topic.relevance_score} style={{ backgroundColor: topic.relevance_score >= 7 ? '#52c41a' : '#faad14' }} overflowCount={10} />
                  }
                >
                  <Card.Meta
                    title={
                      <Space direction="vertical" size={4} style={{ width: '100%' }}>
                        <Text strong>{topic.title}</Text>
                        <Space wrap>
                          <Tag color="blue">{topic.category}</Tag>
                          <Tag color={getDifficultyColor(topic.difficulty)}>
                            {topic.difficulty}
                          </Tag>
                        </Space>
                      </Space>
                    }
                    description={
                      <>
                        <Paragraph ellipsis={{ rows: 3 }} style={{ fontSize: 13 }}>
                          {topic.news_summary}
                        </Paragraph>
                        <Space wrap>
                          {topic.keywords.slice(0, 3).map((kw, idx) => (
                            <Tag key={idx} style={{ fontSize: 11 }}>{kw}</Tag>
                          ))}
                        </Space>
                      </>
                    }
                  />
                </Card>
              </Col>
            ))}
          </Row>
        )}
      </Spin>

      {/* 话题详情弹窗 */}
      <Modal
        title={
          <Space>
            <FireOutlined style={{ color: '#ff4d4f' }} />
            {selectedTopic?.title}
          </Space>
        }
        open={detailVisible}
        onCancel={() => setDetailVisible(false)}
        footer={[
          <Button key="close" onClick={() => setDetailVisible(false)}>
            关闭
          </Button>,
        ]}
        width={800}
        bodyStyle={{ maxHeight: '70vh', overflowY: 'auto' }}
      >
        {selectedTopic && (
          <div>
            {/* 基本信息 */}
            <Card size="small" style={{ marginBottom: 16 }}>
              <Space wrap>
                <Tag color="blue">{selectedTopic.category}</Tag>
                <Tag color={getDifficultyColor(selectedTopic.difficulty)}>
                  {selectedTopic.difficulty}
                </Tag>
                <Tag>相关度: {selectedTopic.relevance_score}/10</Tag>
              </Space>
            </Card>

            {/* 新闻摘要 */}
            <Collapse defaultActiveKey={['1']} style={{ marginBottom: 16 }}>
              <Panel header="📰 热点背景" key="1">
                <Paragraph>{selectedTopic.news_summary}</Paragraph>
                <Space wrap>
                  {selectedTopic.keywords.map((kw, idx) => (
                    <Tag key={idx} icon={<StarOutlined />}>{kw}</Tag>
                  ))}
                </Space>
              </Panel>
            </Collapse>

            {/* 作文题目 */}
            <Card title="📝 模拟作文题目" style={{ marginBottom: 16 }}>
              <MarkdownRenderer content={selectedTopic.essay_prompt} />
            </Card>

            {/* 写作角度 */}
            <Card title="💡 写作角度建议" style={{ marginBottom: 16 }}>
              <ul>
                {selectedTopic.writing_angles.map((angle, idx) => (
                  <li key={idx}>{angle}</li>
                ))}
              </ul>
            </Card>

            {/* 参考素材 */}
            <Card title="📚 参考素材">
              <ul>
                {selectedTopic.reference_materials.map((material, idx) => (
                  <li key={idx}>{material}</li>
                ))}
              </ul>
            </Card>
          </div>
        )}
      </Modal>

      {/* 自定义命题弹窗 */}
      <Modal
        title={
          <Space>
            <BulbOutlined style={{ color: '#faad14' }} />
            自定义命题生成
          </Space>
        }
        open={promptModalVisible}
        onCancel={() => {
          setPromptModalVisible(false);
          setGeneratedPrompt('');
          setCustomKeywords('');
        }}
        footer={null}
        width={800}
        bodyStyle={{ maxHeight: '70vh', overflowY: 'auto' }}
      >
        <div>
          <Text strong>输入关键词</Text>
          <Text type="secondary" style={{ display: 'block', marginBottom: 8 }}>
            多个关键词用逗号或空格分隔，如：科技 人文 平衡
          </Text>
          <Input
            placeholder="输入关键词..."
            value={customKeywords}
            onChange={(e) => setCustomKeywords(e.target.value)}
            onPressEnter={handleGeneratePrompt}
            disabled={generating}
          />
          <Button
            type="primary"
            icon={<BulbOutlined />}
            onClick={handleGeneratePrompt}
            loading={generating}
            block
            style={{ marginTop: 12 }}
          >
            生成作文题目
          </Button>

          {generatedPrompt && (
            <>
              <Divider />
              <Card title="生成的作文题目">
                <MarkdownRenderer content={generatedPrompt} />
              </Card>
            </>
          )}
        </div>
      </Modal>
    </div>
  );
};

export default HotTopicsPage;
