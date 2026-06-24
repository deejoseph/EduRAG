/**
 * 名句和素材模块组件
 * 基于RAG知识库检索名人名言和真实案例,丰富学生知识储备
 */

import React, { useState } from 'react';
import { Card, Tabs, Input, Button, Space, Typography, List, Tag, message, Empty, Spin } from 'antd';
import { SearchOutlined, BookOutlined, LightbulbOutlined, StarOutlined, ExportOutlined } from '@ant-design/icons';
import { writingApi } from '../../api/writing';
import { useWritingStore } from '../../store/writingStore';

const { Text, Paragraph } = Typography;
const { TabPane } = Tabs;

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
  type: string; // 历史事件/人物故事/现实案例
  score: number;
}

interface QuotesAndMaterialsProps {
  topic?: string; // 当前作文题目,用于自动搜索
}

const QuotesAndMaterials: React.FC<QuotesAndMaterialsProps> = ({ topic }) => {
  const [searchTopic, setSearchTopic] = useState(topic || '');
  const [loadingQuotes, setLoadingQuotes] = useState(false);
  const [loadingMaterials, setLoadingMaterials] = useState(false);
  const [quotes, setQuotes] = useState<Quote[]>([]);
  const [materials, setMaterials] = useState<Material[]>([]);
  const [activeTab, setActiveTab] = useState('quotes');

  // 搜索名言
  const handleSearchQuotes = async () => {
    if (!searchTopic.trim()) {
      message.warning('请输入搜索关键词');
      return;
    }

    setLoadingQuotes(true);
    try {
      const response = await writingApi.searchQuotes(searchTopic, 10);
      setQuotes(response.quotes || []);
      if (response.count === 0) {
        message.info('未找到相关名言,请尝试其他关键词');
      } else {
        message.success(`找到 ${response.count} 条相关名言`);
      }
    } catch (error) {
      console.error('搜索名言失败:', error);
      message.error('搜索名言失败');
    } finally {
      setLoadingQuotes(false);
    }
  };

  // 搜索案例
  const handleSearchMaterials = async () => {
    if (!searchTopic.trim()) {
      message.warning('请输入搜索关键词');
      return;
    }

    setLoadingMaterials(true);
    try {
      const response = await writingApi.searchMaterials(searchTopic, 10);
      setMaterials(response.materials || []);
      if (response.count === 0) {
        message.info('未找到相关案例,请尝试其他关键词');
      } else {
        message.success(`找到 ${response.count} 条相关案例`);
      }
    } catch (error) {
      console.error('搜索案例失败:', error);
      message.error('搜索案例失败');
    } finally {
      setLoadingMaterials(false);
    }
  };

  // 导出到播客模块
  const handleExportToPodcast = async (content: string, title: string) => {
    try {
      // 从全局状态获取写作上下文
      const store = useWritingStore.getState();
      await writingApi.exportToPodcast({
        stage: 'essay',
        topic: searchTopic,
        content,
        ai_model: 'rag_search',
        metadata: {
          title,
          generated_at: new Date().toISOString(),
          essay_type: store.topicType || '',
          grade_level: store.gradeLevel || '',
          source: 'quotes_materials',
          content_length: content.length,
        },
      });
      message.success(`✅ "${title}" 已导入播客模块`);
    } catch (error) {
      console.error('导出失败:', error);
      message.error('导出失败');
    }
  };

  // 获取类型标签颜色
  const getTypeColor = (type: string) => {
    const colors: Record<string, string> = {
      '历史事件': 'blue',
      '人物故事': 'green',
      '现实案例': 'orange',
    };
    return colors[type] || 'default';
  };

  return (
    <Card title={<Space><BookOutlined /><span>名句和素材积累</span></Space>} size="small">
      <Space direction="vertical" style={{ width: '100%' }} size="middle">
        {/* 搜索框 */}
        <Space.Compact style={{ width: '100%' }}>
          <Input
            placeholder="输入主题关键词搜索名言和案例(如:奋斗、创新、责任)"
            value={searchTopic}
            onChange={(e) => setSearchTopic(e.target.value)}
            onPressEnter={() => {
              if (activeTab === 'quotes') {
                handleSearchQuotes();
              } else {
                handleSearchMaterials();
              }
            }}
            prefix={<SearchOutlined />}
            allowClear
          />
          <Button
            type="primary"
            icon={<SearchOutlined />}
            onClick={() => {
              if (activeTab === 'quotes') {
                handleSearchQuotes();
              } else {
                handleSearchMaterials();
              }
            }}
          >
            搜索
          </Button>
        </Space.Compact>

        {/* 提示说明 */}
        <Text type="secondary" style={{ fontSize: 12 }}>
          💡 基于RAG知识库智能检索,帮助你积累写作素材,丰富知识储备
        </Text>

        {/* Tab切换 */}
        <Tabs activeKey={activeTab} onChange={setActiveTab}>
          {/* 名人名言选项卡 */}
          <TabPane
            tab={
              <Space>
                <StarOutlined />
                <span>名人名言 ({quotes.length})</span>
              </Space>
            }
            key="quotes"
          >
            <Spin spinning={loadingQuotes}>
              {quotes.length > 0 ? (
                <List
                  dataSource={quotes}
                  renderItem={(quote) => (
                    <List.Item
                      actions={[
                        <Button
                          key="export"
                          type="link"
                          size="small"
                          icon={<ExportOutlined />}
                          onClick={() => handleExportToPodcast(quote.content, `${quote.author}名言`)}
                        >
                          导出
                        </Button>,
                      ]}
                    >
                      <List.Item.Meta
                        title={
                          <Space>
                            <Text strong>{quote.author}</Text>
                            <Tag color="blue">相似度: {(quote.score * 100).toFixed(0)}%</Tag>
                          </Space>
                        }
                        description={
                          <div>
                            <Paragraph
                              ellipsis={{ rows: 3, expandable: true, symbol: '展开' }}
                              style={{ margin: 0, whiteSpace: 'pre-wrap' }}
                            >
                              {quote.content}
                            </Paragraph>
                            <Text type="secondary" style={{ fontSize: 12, marginTop: 4, display: 'block' }}>
                              ——《{quote.source}》
                            </Text>
                          </div>
                        }
                      />
                    </List.Item>
                  )}
                />
              ) : (
                !loadingQuotes && (
                  <Empty
                    description={
                      <Text type="secondary">
                        {searchTopic ? '未找到相关名言,请尝试其他关键词' : '输入关键词后点击搜索'}
                      </Text>
                    }
                    image={Empty.PRESENTED_IMAGE_SIMPLE}
                  />
                )
              )}
            </Spin>
          </TabPane>

          {/* 真实案例选项卡 */}
          <TabPane
            tab={
              <Space>
                <LightbulbOutlined />
                <span>真实案例 ({materials.length})</span>
              </Space>
            }
            key="materials"
          >
            <Spin spinning={loadingMaterials}>
              {materials.length > 0 ? (
                <List
                  dataSource={materials}
                  renderItem={(material) => (
                    <List.Item
                      actions={[
                        <Button
                          key="export"
                          type="link"
                          size="small"
                          icon={<ExportOutlined />}
                          onClick={() => handleExportToPodcast(material.content, material.title)}
                        >
                          导出
                        </Button>,
                      ]}
                    >
                      <List.Item.Meta
                        title={
                          <Space>
                            <Text strong>{material.title}</Text>
                            <Tag color={getTypeColor(material.type)}>{material.type}</Tag>
                            <Tag color="blue">相似度: {(material.score * 100).toFixed(0)}%</Tag>
                          </Space>
                        }
                        description={
                          <Paragraph
                            ellipsis={{ rows: 4, expandable: true, symbol: '展开' }}
                            style={{ margin: 0, whiteSpace: 'pre-wrap' }}
                          >
                            {material.content}
                          </Paragraph>
                        }
                      />
                    </List.Item>
                  )}
                />
              ) : (
                !loadingMaterials && (
                  <Empty
                    description={
                      <Text type="secondary">
                        {searchTopic ? '未找到相关案例,请尝试其他关键词' : '输入关键词后点击搜索'}
                      </Text>
                    }
                    image={Empty.PRESENTED_IMAGE_SIMPLE}
                  />
                )
              )}
            </Spin>
          </TabPane>
        </Tabs>
      </Space>
    </Card>
  );
};

export default QuotesAndMaterials;
