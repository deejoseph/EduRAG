/**
 * 名句和素材积累模块 - 简化版本(用于排查问题)
 */

import React, { useState } from 'react';
import { Card, Tabs, Input, Button, Space, Typography, message, Statistic, Row, Col, Divider } from 'antd';
import { SearchOutlined, BookOutlined, StarOutlined, CheckCircleOutlined, LightbulbOutlined } from '@ant-design/icons';

const { Text } = Typography;
const { TabPane } = Tabs;

const QuotesAndMaterialsSimple: React.FC = () => {
  const [searchTopic, setSearchTopic] = useState('');
  const [activeTab, setActiveTab] = useState('quotes');
  
  // 学习统计
  const stats = {
    total_quotes: 0,
    total_materials: 0,
    learned_quotes: 0,
    learned_materials: 0,
  };

  console.log('[Simple] 简化版名句素材页面已加载');

  const handleSearch = () => {
    if (!searchTopic.trim()) {
      message.warning('请输入搜索关键词');
      return;
    }
    message.info(`搜索: ${searchTopic}`);
  };

  return (
    <div style={{ padding: 24 }}>
      <Card title={<Space><BookOutlined /><span>名句和素材积累</span></Space>} size="small">
        <Space direction="vertical" style={{ width: '100%' }} size="large">
          {/* 学习统计 */}
          <Row gutter={16}>
            <Col span={6}>
              <Statistic 
                title="名言总数" 
                value={stats.total_quotes} 
                prefix={<StarOutlined />}
              />
            </Col>
            <Col span={6}>
              <Statistic 
                title="已学名言" 
                value={stats.learned_quotes}
                valueStyle={{ color: '#3f8600' }}
                prefix={<CheckCircleOutlined />}
              />
            </Col>
            <Col span={6}>
              <Statistic 
                title="案例总数" 
                value={stats.total_materials}
                prefix={<LightbulbOutlined />}
              />
            </Col>
            <Col span={6}>
              <Statistic 
                title="已学案例" 
                value={stats.learned_materials}
                valueStyle={{ color: '#3f8600' }}
                prefix={<CheckCircleOutlined />}
              />
            </Col>
          </Row>

          <Divider />

          {/* 搜索框 */}
          <Space.Compact style={{ width: '100%' }}>
            <Input
              placeholder="输入主题关键词搜索名言和案例(如:奋斗、创新、责任)"
              value={searchTopic}
              onChange={(e) => setSearchTopic(e.target.value)}
              onPressEnter={handleSearch}
              prefix={<SearchOutlined />}
              allowClear
            />
            <Button
              type="primary"
              icon={<SearchOutlined />}
              onClick={handleSearch}
            >
              搜索
            </Button>
          </Space.Compact>

          <Text type="secondary" style={{ fontSize: 12 }}>
            💡 基于RAG知识库智能检索,支持AI自动搜索并保存新内容。
          </Text>

          {/* Tab切换 */}
          <Tabs activeKey={activeTab} onChange={setActiveTab}>
            <TabPane
              tab={
                <Space>
                  <StarOutlined />
                  <span>名人名言</span>
                </Space>
              }
              key="quotes"
            >
              <div style={{ padding: 20, textAlign: 'center', color: '#999' }}>
                暂无数据,请先搜索
              </div>
            </TabPane>

            <TabPane
              tab={
                <Space>
                  <StarOutlined />
                  <span>真实案例</span>
                </Space>
              }
              key="materials"
            >
              <div style={{ padding: 20, textAlign: 'center', color: '#999' }}>
                暂无数据,请先搜索
              </div>
            </TabPane>
          </Tabs>
        </Space>
      </Card>
    </div>
  );
};

export default QuotesAndMaterialsSimple;
