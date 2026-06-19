import React, { useEffect, useState } from 'react';
import {
  Card, Row, Col, Tag, Button, Select, Space, Typography, Spin,
  message, Divider, Collapse, Modal, Input, Alert, Badge, Empty, Popconfirm,
} from 'antd';
import {
  FireOutlined, ReloadOutlined, BulbOutlined,
  SearchOutlined, StarOutlined, StarFilled,
  HistoryOutlined, DownloadOutlined,
} from '@ant-design/icons';
import type { TopicCategory, HotTopic } from '../../types/hotTopics';
import {
  getCategories, searchHotTopics, refreshCache, generateCustomPrompt,
  favoriteTopic, unfavoriteTopic, getFavorites, getHotTopicsStats,
  favoriteAllTopics,
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
  
  // 收藏相关状态
  const [favorites, setFavorites] = useState<HotTopic[]>([]);
  const [favoritedTitles, setFavoritedTitles] = useState<Set<string>>(new Set());
  const [showFavoritesOnly, setShowFavoritesOnly] = useState(false);

  // 自定义命题弹窗
  const [promptModalVisible, setPromptModalVisible] = useState(false);
  const [customKeywords, setCustomKeywords] = useState('');
  const [generatedPrompt, setGeneratedPrompt] = useState<string>('');
  const [generating, setGenerating] = useState(false);

  // 话题详情弹窗
  const [detailVisible, setDetailVisible] = useState(false);
  const [selectedTopic, setSelectedTopic] = useState<HotTopic | null>(null);
  
  // 历史热门主题相关状态
  const [hotTopicsStats, setHotTopicsStats] = useState<Array<{
    name: string;
    keywords: string[];
    count: number;
    max_score: number;
    description: string;
  }>>([]);
  const [loadingHotTopics, setLoadingHotTopics] = useState(false);
  
  // 加载收藏列表
  useEffect(() => {
    loadFavorites();
  }, []);
  
  const loadFavorites = async () => {
    try {
      const res = await getFavorites();
      setFavorites(res.topics);
      setFavoritedTitles(new Set(res.topics.map(t => t.title)));
    } catch (error) {
      console.error('加载收藏失败:', error);
    }
  };

  // 加载历史热门主题统计
  useEffect(() => {
    loadHotTopicsStats();
  }, []);

  const loadHotTopicsStats = async () => {
    try {
      setLoadingHotTopics(true);
      const res = await getHotTopicsStats();
      setHotTopicsStats(res.topics);
    } catch (error) {
      console.error('加载热门主题统计失败:', error);
    } finally {
      setLoadingHotTopics(false);
    }
  };

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
    
    // 显示初始提示
    message.info('🔍 开始分析热点话题...', 2);
    
    try {
      // 显示加载状态，不自动关闭
      message.loading('正在连接后端服务...', 0);
      
      const startTime = Date.now();
      
      // 定期更新进度提示
      const progressTimer = setInterval(() => {
        const elapsed = Math.floor((Date.now() - startTime) / 1000);
        if (elapsed < 5) {
          message.destroy();
          message.loading(`正在分析社会热点... (${elapsed}秒)`, 0);
        } else if (elapsed < 15) {
          message.destroy();
          message.loading(`LLM正在生成命题预测... (${elapsed}秒)`, 0);
        } else if (elapsed < 30) {
          message.destroy();
          message.warning(`⏱️ LLM响应较慢，系统将使用示例数据... (${elapsed}秒)`, 2);
        } else {
          message.destroy();
          message.warning(`仍在处理中，请稍候... (${elapsed}秒)`, 2);
        }
      }, 3000);
      
      const res = await searchHotTopics({
        category_id: selectedCategory,
        use_cache: true,
      });
      
      // 清除定时器
      clearInterval(progressTimer);
      message.destroy();
      
      const elapsedTime = Math.floor((Date.now() - startTime) / 1000);
      
      setTopics(res.topics);
      
      if (res.topics.length === 0) {
        message.warning('暂无热点数据，请点击"刷新缓存"按钮重新生成', 3);
      } else {
        // 检查是否使用了降级数据（通过检查是否有"示例"字样）
        const hasFallbackData = res.topics.some(t => 
          t.title.includes('人工智能与人类创造力') || 
          t.title.includes('数字时代的') ||
          t.title.includes('算法推荐')
        );
        
        if (hasFallbackData && elapsedTime > 20) {
          message.warning(
            `⚠️ LLM响应超时，已显示示例数据（耗时 ${elapsedTime} 秒）。如需真实数据，请点击"刷新缓存"`, 
            5
          );
        } else {
          message.success(
            `✅ 成功获取 ${res.topics.length} 个热点话题（耗时 ${elapsedTime} 秒）`, 
            3
          );
        }
      }
    } catch (error: any) {
      message.destroy();
      const errorMsg = error?.response?.data?.error || error?.message || '搜索失败，请重试';
      message.error(`❌ ${errorMsg}`, 5);
      console.error('搜索热点话题失败:', error);
    } finally {
      setLoading(false);
    }
  };

  // 刷新缓存
  const handleRefresh = async () => {
    setRefreshing(true);
    
    message.info('🔄 开始刷新热点数据...', 2);
    
    try {
      message.loading('正在清除旧缓存...', 0);
      
      const startTime = Date.now();
      
      // 定期更新进度
      const progressTimer = setInterval(() => {
        const elapsed = Math.floor((Date.now() - startTime) / 1000);
        message.destroy();
        message.loading(`正在重新生成热点数据... (${elapsed}秒)`, 0);
      }, 3000);
      
      await refreshCache({
        category_id: selectedCategory,
      });
      
      clearInterval(progressTimer);
      message.destroy();
      
      const elapsedTime = Math.floor((Date.now() - startTime) / 1000);
      message.success(`✅ 刷新成功（耗时 ${elapsedTime} 秒）`, 2);
      
      // 刷新后自动重新搜索
      handleSearch();
    } catch (error: any) {
      message.destroy();
      const errorMsg = error?.response?.data?.error || error?.message || '刷新失败';
      message.error(`❌ ${errorMsg}`, 5);
      console.error('刷新缓存失败:', error);
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
  
  // 收藏/取消收藏
  const handleToggleFavorite = async (topic: HotTopic) => {
    const isFavorited = favoritedTitles.has(topic.title);
    
    try {
      if (isFavorited) {
        await unfavoriteTopic(topic.title);
        message.success('已取消收藏');
      } else {
        await favoriteTopic(topic);
        message.success('已添加到题库');
      }
      
      // 重新加载收藏列表
      await loadFavorites();
    } catch (error: any) {
      if (error.response?.status === 409) {
        message.warning('该话题已在收藏中');
      } else {
        message.error('操作失败，请重试');
      }
    }
  };

  // 一键收藏所有当前话题
  const handleFavoriteAll = async () => {
    if (topics.length === 0) {
      message.warning('当前没有可收藏的话题');
      return;
    }

    try {
      const res = await favoriteAllTopics(topics);
      message.success(res.message);
      // 重新加载收藏列表
      await loadFavorites();
    } catch (error: any) {
      const errorMsg = error?.response?.data?.error || error?.message || '一键收藏失败';
      message.error(errorMsg);
    }
  };
  
  // 获取当前显示的话题列表
  const getDisplayedTopics = () => {
    if (showFavoritesOnly) {
      return favorites;
    }
    return topics;
  };

  // 点击热门主题进行搜索
  const handleSearchByHotTopic = async (topicName: string, keywords: string[]) => {
    setLoading(true);
    
    message.info(`🔍 正在分析"${topicName}"相关命题...`, 2);
    
    try {
      message.loading('正在连接后端服务...', 0);
      
      const startTime = Date.now();
      
      // 定期更新进度提示
      const progressTimer = setInterval(() => {
        const elapsed = Math.floor((Date.now() - startTime) / 1000);
        if (elapsed < 5) {
          message.destroy();
          message.loading(`正在分析"${topicName}"主题... (${elapsed}秒)`, 0);
        } else if (elapsed < 15) {
          message.destroy();
          message.loading(`LLM正在生成命题预测... (${elapsed}秒)`, 0);
        } else if (elapsed < 30) {
          message.destroy();
          message.warning(`⏱️ LLM响应较慢，请耐心等待... (${elapsed}秒)`, 2);
        } else {
          message.destroy();
          message.warning(`仍在处理中，请稍候... (${elapsed}秒)`, 2);
        }
      }, 3000);
      
      // 使用关键词作为搜索条件，调用后端API
      const res = await searchHotTopics({
        keywords: keywords,
        topic_name: topicName,
        use_cache: true,
      });
      
      // 清除定时器
      clearInterval(progressTimer);
      message.destroy();
      
      const elapsedTime = Math.floor((Date.now() - startTime) / 1000);
      
      setTopics(res.topics);
      
      if (res.topics.length === 0) {
        message.warning(`未能生成与"${topicName}"相关的命题预测，请重试`, 3);
      } else {
        message.success(
          `✅ 成功获取"${topicName}"相关命题预测（共 ${res.topics.length} 个，耗时 ${elapsedTime} 秒）`, 
          3
        );
      }
    } catch (error: any) {
      message.destroy();
      const errorMsg = error?.response?.data?.error || error?.message || '搜索失败，请重试';
      message.error(`❌ ${errorMsg}`, 5);
      console.error('搜索热点话题失败:', error);
    } finally {
      setLoading(false);
    }
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
            <Divider style={{ margin: '12px 0' }} />
            <p style={{ marginBottom: 0 }}>
              <Text type="secondary">
                💡 <strong>提示：</strong>首次搜索可能需要等待 LLM 响应（最长120秒）。如果超时，系统将自动显示示例数据。
                点击"刷新缓存"可尝试重新生成真实数据。
              </Text>
            </p>
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
            icon={<StarFilled />}
            type={showFavoritesOnly ? 'primary' : 'default'}
            onClick={() => setShowFavoritesOnly(!showFavoritesOnly)}
          >
            我的题库 ({favorites.length})
          </Button>

          <Button
            icon={<DownloadOutlined />}
            onClick={handleFavoriteAll}
            disabled={topics.length === 0 || showFavoritesOnly}
            title={topics.length > 0 ? `一键收藏当前 ${topics.length} 个话题` : '请先搜索话题'}
          >
            一键收藏
          </Button>

          <Button
            icon={<BulbOutlined />}
            onClick={() => setPromptModalVisible(true)}
          >
            自定义命题
          </Button>
        </Space>
        
        {/* 进度提示 */}
        {(loading || refreshing) && (
          <div style={{ marginTop: 16, padding: 12, background: '#f0f9ff', borderRadius: 8, border: '1px solid #91caff' }}>
            <Space direction="vertical" size="small" style={{ width: '100%' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <Spin size="small" />
                <Text strong style={{ color: '#0958d9' }}>
                  {loading ? '正在搜索热点话题...' : '正在刷新缓存...'}
                </Text>
              </div>
              <Text type="secondary" style={{ fontSize: 12 }}>
                💡 系统正在执行以下操作：
              </Text>
              <ul style={{ margin: 0, paddingLeft: 20, fontSize: 12, color: '#666' }}>
                <li>分析当前社会热点和教育动态</li>
                <li>调用AI模型生成高考作文命题预测</li>
                <li>整理写作角度和参考素材</li>
                <li>预计耗时：使用缓存约5-10秒，重新生成约1-3分钟</li>
              </ul>
            </Space>
          </div>
        )}
      </Card>

      {/* 历史热门主题快速搜索 */}
      <Card 
        title={
          <Space>
            <HistoryOutlined style={{ color: '#faad14' }} />
            按历史热门主题搜索
          </Space>
        }
        style={{ marginBottom: 24 }}
        loading={loadingHotTopics}
      >
        <Text type="secondary" style={{ display: 'block', marginBottom: 12 }}>
          点击下方主题标签，基于知识库统计的热门主题生成相关命题预测
        </Text>
        <Space wrap size="middle">
          {hotTopicsStats.map((topic, index) => (
            <Card
              key={index}
              hoverable
              style={{ width: 200, cursor: 'pointer' }}
              onClick={() => handleSearchByHotTopic(topic.name, topic.keywords)}
            >
              <Card.Meta
                title={
                  <Space>
                    <FireOutlined style={{ color: '#ff4d4f' }} />
                    {topic.name}
                  </Space>
                }
                description={
                  <>
                    <Text type="secondary" style={{ fontSize: 12 }}>
                      {topic.description}
                    </Text>
                    <div style={{ marginTop: 8 }}>
                      <Badge count={topic.count} overflowCount={99} style={{ backgroundColor: '#52c41a' }} />
                      <Text type="secondary" style={{ fontSize: 11, marginLeft: 8 }}>
                        相关度: {(topic.max_score * 100).toFixed(0)}%
                      </Text>
                    </div>
                    <Space wrap style={{ marginTop: 8 }}>
                      {topic.keywords.slice(0, 3).map((kw, idx) => (
                        <Tag key={idx} style={{ fontSize: 10 }}>{kw}</Tag>
                      ))}
                    </Space>
                  </>
                }
              />
            </Card>
          ))}
        </Space>
      </Card>

      {/* 热点话题列表 */}
      <Spin spinning={loading}>
        {getDisplayedTopics().length === 0 ? (
          <Card>
            <Empty
              description={showFavoritesOnly ? '暂无收藏的话题，点击话题卡片上的星号图标添加到题库' : '点击"搜索热点"按钮开始分析'}
              image={Empty.PRESENTED_IMAGE_SIMPLE}
            />
          </Card>
        ) : (
          <Row gutter={[16, 16]}>
            {getDisplayedTopics().map((topic, index) => {
              const isFavorited = favoritedTitles.has(topic.title);
              
              return (
                <Col xs={24} sm={12} lg={8} key={index}>
                  <Card
                    hoverable
                    onClick={() => handleViewDetail(topic)}
                    extra={
                      <Space size="small">
                        <Badge count={topic.relevance_score} style={{ backgroundColor: topic.relevance_score >= 7 ? '#52c41a' : '#faad14' }} overflowCount={10} />
                        <Popconfirm
                          title={isFavorited ? "确定取消收藏？" : "添加到题库？"}
                          onConfirm={(e) => {
                            e?.stopPropagation();
                            handleToggleFavorite(topic);
                          }}
                          okText="确定"
                          cancelText="取消"
                        >
                          <Button
                            type={isFavorited ? 'primary' : 'default'}
                            size="small"
                            icon={isFavorited ? <StarFilled /> : <StarOutlined />}
                            onClick={(e) => e.stopPropagation()}
                            title={isFavorited ? '取消收藏' : '添加到题库'}
                          />
                        </Popconfirm>
                      </Space>
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
              );
            })}
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
