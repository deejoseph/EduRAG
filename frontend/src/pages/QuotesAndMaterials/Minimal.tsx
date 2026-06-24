import React, { useState, useEffect } from 'react';
import { Tabs, Input, Button, Space, message, List, Card, Tag, Typography, Pagination } from 'antd';
import { SearchOutlined, StarOutlined, BulbOutlined, ReloadOutlined } from '@ant-design/icons';
import { writingApi } from '../../api/writing';
import apiClient from '../../api/client';

const { TabPane } = Tabs;
const { Text } = Typography;

interface Quote {
  id: string;
  content: string;
  author: string;
  source: string;
  score: number;
}

interface Material {
  id: string;
  title: string;
  content: string;
  type: string;
  score: number;
}

const QuotesAndMaterialsMinimal: React.FC = () => {
  const [activeTab, setActiveTab] = useState('quotes');
  const [searchTopic, setSearchTopic] = useState('');
  const [loading, setLoading] = useState(false);
  const [quotes, setQuotes] = useState<Quote[]>([]);
  const [materials, setMaterials] = useState<Material[]>([]);
  const [allQuotes, setAllQuotes] = useState<Quote[]>([]); // 所有名言
  const [loadingQuotes, setLoadingQuotes] = useState(false);
  
  // 分页状态
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize] = useState(50); // 每页50条
  const [totalQuotes, setTotalQuotes] = useState(0); // 总数量
  
  console.log('[Minimal] 极简版名句素材页面已加载');
  
  // 页面加载时从知识库获取所有名言
  useEffect(() => {
    loadAllQuotes();
  }, []);
  
  // 从知识库加载名言（支持分页）
  const loadAllQuotes = async (page: number = 1) => {
    console.log(`[loadAllQuotes] 开始加载第${page}页名言...`);
    setLoadingQuotes(true);
    try {
      // 尝试从后端API获取名言列表
      console.log(`[loadAllQuotes] 发送API请求: /quotes/list?page=${page}&limit=${pageSize}`);
      const response = await apiClient.get('/quotes/list', {
        params: { page, limit: pageSize }
      });
      
      console.log('[loadAllQuotes] API响应:', response);
      
      if (response && response.success) {
        const formattedQuotes = response.quotes.map((q: any) => ({
          id: q.id,
          content: q.text,
          author: q.author,
          source: q.category || '名人名言',
          score: 1.0
        }));
        setAllQuotes(formattedQuotes);
        setQuotes(formattedQuotes); // 默认显示所有名言
        setTotalQuotes(response.pagination?.total || formattedQuotes.length); // 设置总数
        setCurrentPage(page); // 更新当前页码
        console.log(`[知识库] 成功加载第${page}页，共${formattedQuotes.length}条名言，总计${response.pagination?.total || 0}条`);
      } else {
        console.warn('[loadAllQuotes] API返回success=false，使用示例数据');
        throw new Error('API返回失败');
      }
    } catch (error: any) {
      console.error('[loadAllQuotes] 加载失败，使用示例数据:', error.message || error);
      // API失败时，显示示例名言
      const sampleQuotes: Quote[] = [
        {
          id: 'sample_1',
          content: '学而不思则罔，思而不学则殆。',
          author: '孔子',
          source: '《论语》',
          score: 1.0
        },
        {
          id: 'sample_2',
          content: '读书破万卷，下笔如有神。',
          author: '杜甫',
          source: '《奉赠韦左丞丈二十二韵》',
          score: 1.0
        },
        {
          id: 'sample_3',
          content: '不积跬步，无以至千里；不积小流，无以成江海。',
          author: '荀子',
          source: '《劝学》',
          score: 1.0
        },
        {
          id: 'sample_4',
          content: '天行健，君子以自强不息。',
          author: '周易',
          source: '《周易》',
          score: 1.0
        },
        {
          id: 'sample_5',
          content: '路漫漫其修远兮，吾将上下而求索。',
          author: '屈原',
          source: '《离骚》',
          score: 1.0
        }
      ];
      setAllQuotes(sampleQuotes);
      setQuotes(sampleQuotes);
      setTotalQuotes(sampleQuotes.length);
      console.log('[示例数据] 已加载5条示例名言');
    } finally {
      setLoadingQuotes(false);
      console.log('[loadAllQuotes] 加载完成');
    }
  };
  
  // 刷新名言列表
  const handleRefresh = () => {
    loadAllQuotes(1); // 刷新时回到第一页
    message.success('已刷新名言列表');
  };
  
  // 搜索功能：同时搜索名言和案例
  const handleSearch = async () => {
    if (!searchTopic.trim()) {
      message.warning('请输入搜索关键词');
      return;
    }
    
    setLoading(true);
    try {
      // 同时搜索名言和案例
      const [quotesResult, materialsResult] = await Promise.all([
        writingApi.searchQuotes(searchTopic, 10),
        writingApi.searchMaterials(searchTopic, 10),
      ]);
      
      setQuotes(quotesResult.quotes || []);
      setMaterials(materialsResult.materials || []);
      
      const total = (quotesResult.quotes?.length || 0) + (materialsResult.materials?.length || 0);
      if (total === 0) {
        message.info('知识库中暂无相关内容，请点击"AI生成"生成新内容');
      } else {
        message.success(`找到 ${quotesResult.quotes?.length || 0} 条名言，${materialsResult.materials?.length || 0} 个案例`);
      }
    } catch (error: any) {
      console.error('[搜索] 失败:', error);
      message.error(error.message || '搜索失败');
    } finally {
      setLoading(false);
    }
  };
  
  // AI生成并保存
  const handleAIGenerate = async () => {
    if (!searchTopic.trim()) {
      message.warning('请输入搜索关键词');
      return;
    }
    
    setLoading(true);
    try {
      const result = await writingApi.aiSearchAndSave(searchTopic);
      message.success(`AI生成完成! 保存了 ${result.saved_count} 条内容`);
      
      // 生成完成后自动搜索显示新内容
      setTimeout(() => {
        handleSearch();
      }, 500);
    } catch (error: any) {
      console.error('AI生成失败:', error);
      message.error(error.message || 'AI生成失败');
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <div style={{ padding: 24 }}>
      <h1>名句和素材模块 - 极简版</h1>
      <p>这是最简单的测试页面</p>
      
      {/* 搜索框 */}
      <Space style={{ marginBottom: 16 }} size="middle">
        <Input
          placeholder="输入关键词搜索名句和素材(如:奋斗、创新、责任)"
          value={searchTopic}
          onChange={(e) => setSearchTopic(e.target.value)}
          onPressEnter={handleSearch}
          style={{ width: 400 }}
          prefix={<SearchOutlined />}
        />
        <Button
          type="primary"
          icon={<SearchOutlined />}
          onClick={handleSearch}
          loading={loading}
        >
          搜索
        </Button>
        <Button
          type="default"
          onClick={handleAIGenerate}
          loading={loading}
        >
          AI生成
        </Button>
      </Space>
      
      <Tabs
        activeKey={activeTab}
        onChange={(key) => setActiveTab(key)}
        tabBarExtraContent={
          activeTab === 'quotes' ? (
            <Button
              icon={<ReloadOutlined />}
              onClick={handleRefresh}
              loading={loadingQuotes}
              size="small"
            >
              刷新
            </Button>
          ) : null
        }
      >
        <TabPane 
          tab={
            <span>
              <StarOutlined />
              名人名言 ({totalQuotes > 0 ? totalQuotes : quotes.length})
            </span>
          } 
          key="quotes"
        >
          <div style={{ padding: 16 }}>
            {loadingQuotes ? (
              <Typography.Text type="secondary">加载中...</Typography.Text>
            ) : quotes.length === 0 ? (
              <Typography.Text type="secondary">暂无名言数据</Typography.Text>
            ) : allQuotes.length > 0 && quotes.length === allQuotes.length ? (
              <div>
                <Typography.Text type="success" style={{ marginBottom: 8, display: 'block' }}>
                  ✓ 已从知识库加载 {quotes.length} 条名言
                </Typography.Text>
                <List
                  dataSource={quotes}
                  renderItem={(item) => (
                    <Card size="small" style={{ marginBottom: 8 }}>
                      <div style={{ marginBottom: 8 }}>
                        <Text strong>{item.content}</Text>
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <Space size="small">
                          <Tag color="blue">{item.author}</Tag>
                          <Tag color="green">{item.source}</Tag>
                        </Space>
                        {item.score && item.score < 1.0 && (
                          <Text type="secondary" style={{ fontSize: 12 }}>相似度: {(item.score * 100).toFixed(1)}%</Text>
                        )}
                      </div>
                    </Card>
                  )}
                />
                {/* 分页控件 */}
                {totalQuotes > pageSize && (
                  <div style={{ marginTop: 16, textAlign: 'center' }}>
                    <Pagination
                      current={currentPage}
                      total={totalQuotes}
                      pageSize={pageSize}
                      showSizeChanger={false}
                      showQuickJumper
                      showTotal={(total) => `共 ${total} 条名言`}
                      onChange={(page) => loadAllQuotes(page)}
                    />
                  </div>
                )}
              </div>
            ) : (
              <List
                dataSource={quotes}
                renderItem={(item) => (
                  <Card size="small" style={{ marginBottom: 8 }}>
                    <div style={{ marginBottom: 8 }}>
                      <Text strong>{item.content}</Text>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <Space size="small">
                        <Tag color="blue">{item.author}</Tag>
                        <Tag color="green">{item.source}</Tag>
                      </Space>
                      {item.score && item.score < 1.0 && (
                        <Text type="secondary" style={{ fontSize: 12 }}>相似度: {(item.score * 100).toFixed(1)}%</Text>
                      )}
                    </div>
                  </Card>
                )}
              />
            )}
          </div>
        </TabPane>
        <TabPane 
          tab={
            <span>
              <BulbOutlined />
              真实案例 ({materials.length})
            </span>
          } 
          key="materials"
        >
          <div style={{ padding: 16 }}>
            {materials.length === 0 ? (
              <Typography.Text type="secondary">暂无搜索结果，请尝试搜索或AI生成</Typography.Text>
            ) : (
              <List
                dataSource={materials}
                renderItem={(item) => (
                  <Card size="small" style={{ marginBottom: 8 }}>
                    <div style={{ marginBottom: 8 }}>
                      <Text strong>{item.title}</Text>
                      <Tag color="purple" style={{ marginLeft: 8 }}>{item.type}</Tag>
                    </div>
                    <div style={{ marginBottom: 8 }}>
                      <Text>{item.content}</Text>
                    </div>
                    <Text type="secondary" style={{ fontSize: 12 }}>相似度: {(item.score * 100).toFixed(1)}%</Text>
                  </Card>
                )}
              />
            )}
          </div>
        </TabPane>
      </Tabs>
    </div>
  );
};

export default QuotesAndMaterialsMinimal;
