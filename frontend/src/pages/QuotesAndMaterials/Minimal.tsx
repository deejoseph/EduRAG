import React, { useState } from 'react';
import { Tabs, Input, Button, Space, message, List, Card, Tag, Typography } from 'antd';
import { SearchOutlined, StarOutlined, BulbOutlined } from '@ant-design/icons';
import { writingApi } from '../../api/writing';

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
  
  console.log('[Minimal] 极简版名句素材页面已加载');
  
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
      >
        <TabPane 
          tab={
            <span>
              <StarOutlined />
              名人名言 ({quotes.length})
            </span>
          } 
          key="quotes"
        >
          <div style={{ padding: 16 }}>
            {quotes.length === 0 ? (
              <Typography.Text type="secondary">暂无搜索结果，请尝试搜索或AI生成</Typography.Text>
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
                      <Text type="secondary" style={{ fontSize: 12 }}>相似度: {(item.score * 100).toFixed(1)}%</Text>
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
