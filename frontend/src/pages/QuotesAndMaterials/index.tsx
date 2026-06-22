/**
 * 名句和素材积累模块 - 独立页面
 * 基于RAG知识库检索名人名言和真实案例,支持AI搜索、学习追踪、编辑管理
 */

import React, { useState, useEffect } from 'react';
import { 
  Card, Tabs, Input, Button, Space, Typography, List, Tag, message, Empty, Spin, 
  Modal, Form, Select, Divider, Statistic, Row, Col, Popconfirm
} from 'antd';
import { 
  SearchOutlined, BookOutlined, LightbulbOutlined, StarOutlined, ExportOutlined,
  EditOutlined, DeleteOutlined, CheckCircleOutlined, CloudUploadOutlined
} from '@ant-design/icons';
import { writingApi } from '../../api/writing';

const { Text, Paragraph } = Typography;
const { TabPane } = Tabs;
const { TextArea } = Input;

interface Quote {
  id: string;
  content: string;
  author: string;
  source: string;
  score?: number;
  is_learned?: boolean;
  created_at?: string;
}

interface Material {
  id: string;
  title: string;
  content: string;
  type: string; // 历史事件/人物故事/现实案例
  score?: number;
  is_learned?: boolean;
  created_at?: string;
}

interface LearningStats {
  total_quotes: number;
  total_materials: number;
  learned_quotes: number;
  learned_materials: number;
}

const QuotesAndMaterialsPage: React.FC = () => {
  const [searchTopic, setSearchTopic] = useState('');
  const [loadingQuotes, setLoadingQuotes] = useState(false);
  const [loadingMaterials, setLoadingMaterials] = useState(false);
  const [quotes, setQuotes] = useState<Quote[]>([]);
  const [materials, setMaterials] = useState<Material[]>([]);
  const [activeTab, setActiveTab] = useState('quotes');
  
  // 学习统计
  const [stats, setStats] = useState<LearningStats>({
    total_quotes: 0,
    total_materials: 0,
    learned_quotes: 0,
    learned_materials: 0,
  });
  
  // 编辑弹窗
  const [editModalVisible, setEditModalVisible] = useState(false);
  const [editingItem, setEditingItem] = useState<Quote | Material | null>(null);
  const [editForm] = Form.useForm();
  
  // AI搜索加载状态
  const [aiSearching, setAiSearching] = useState(false);

  // 加载学习统计
  useEffect(() => {
    loadLearningStats();
  }, []);

  const loadLearningStats = async () => {
    try {
      // TODO: 调用后端API获取学习统计
      // const response = await writingApi.getQuotesMaterialsStats();
      // setStats(response.stats);
      
      // 临时模拟数据
      setStats({
        total_quotes: quotes.length,
        total_materials: materials.length,
        learned_quotes: quotes.filter(q => q.is_learned).length,
        learned_materials: materials.filter(m => m.is_learned).length,
      });
    } catch (error) {
      console.error('加载学习统计失败:', error);
    }
  };

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
      loadLearningStats();
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
      loadLearningStats();
    } catch (error) {
      console.error('搜索案例失败:', error);
      message.error('搜索案例失败');
    } finally {
      setLoadingMaterials(false);
    }
  };

  // AI智能搜索并保存到知识库
  const handleAISearch = async () => {
    if (!searchTopic.trim()) {
      message.warning('请输入搜索关键词');
      return;
    }
  
    Modal.confirm({
      title: 'AI智能搜索',
      content: `将使用AI搜索“${searchTopic}”相关的名句和素材,并保存到知识库。这可能需要几分钟时间,是否继续?`,
      okText: '开始搜索',
      cancelText: '取消',
      onOk: async () => {
        setAiSearching(true);
        try {
          await writingApi.aiSearchAndSave(searchTopic);
          message.success('AI搜索完成,新内容已保存到知识库');
          loadLearningStats();
          // 重新搜索以显示新内容
          if (activeTab === 'quotes') {
            handleSearchQuotes();
          } else {
            handleSearchMaterials();
          }
        } catch (error) {
          console.error('AI搜索失败:', error);
          message.error('AI搜索失败');
        } finally {
          setAiSearching(false);
        }
      }
    });
  };

  // 标记为已学习
  const handleMarkAsLearned = async (id: string, type: 'quote' | 'material') => {
    try {
      // TODO: 调用后端API标记已学习(需要实现学习记录表)
      // await writingApi.markQuoteOrMaterialLearned(id, type);
      
      if (type === 'quote') {
        setQuotes(prev => prev.map(q => 
          q.id === id ? { ...q, is_learned: !q.is_learned } : q
        ));
      } else {
        setMaterials(prev => prev.map(m => 
          m.id === id ? { ...m, is_learned: !m.is_learned } : m
        ));
      }
      
      message.success('学习状态已更新');
      loadLearningStats();
    } catch (error) {
      console.error('更新学习状态失败:', error);
      message.error('更新失败');
    }
  };

  // 打开编辑弹窗
  const handleOpenEditModal = (item: Quote | Material) => {
    setEditingItem(item);
    editForm.setFieldsValue({
      content: item.content,
      author: (item as Quote).author || '',
      source: (item as Quote).source || '',
      title: (item as Material).title || '',
      type: (item as Material).type || '',
    });
    setEditModalVisible(true);
  };

  // 保存编辑
  const handleSaveEdit = async () => {
    try {
      const values = await editForm.validateFields();
      
      if (!editingItem) return;
      
      const updateData: any = {
        type: activeTab === 'quotes' ? 'quote' : 'material',
        ...values,
      };
      
      await writingApi.updateQuoteOrMaterial(editingItem.id, updateData);
      
      message.success('修改成功');
      setEditModalVisible(false);
      setEditingItem(null);
      
      // 刷新列表
      if (activeTab === 'quotes') {
        handleSearchQuotes();
      } else {
        handleSearchMaterials();
      }
    } catch (error) {
      console.error('保存失败:', error);
      message.error('保存失败');
    }
  };

  // 删除
  const handleDelete = async (id: string, type: 'quote' | 'material') => {
    try {
      await writingApi.deleteQuoteOrMaterial(id);
      
      message.success('删除成功');
      
      if (type === 'quote') {
        setQuotes(prev => prev.filter(q => q.id !== id));
      } else {
        setMaterials(prev => prev.filter(m => m.id !== id));
      }
      
      loadLearningStats();
    } catch (error) {
      console.error('删除失败:', error);
      message.error('删除失败');
    }
  };

  // 导出到播客模块
  const handleExportToPodcast = async (content: string, title: string) => {
    try {
      await writingApi.exportToPodcast({
        stage: 'essay',
        topic: searchTopic,
        content,
        ai_model: 'rag_search',
        metadata: {
          title,
          generated_at: new Date().toISOString(),
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

          {/* 搜索框和操作按钮 */}
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
            <Button
              type="default"
              icon={<CloudUploadOutlined />}
              loading={aiSearching}
              onClick={handleAISearch}
            >
              AI搜索并保存
            </Button>
          </Space.Compact>

          {/* 提示说明 */}
          <Text type="secondary" style={{ fontSize: 12 }}>
            💡 基于RAG知识库智能检索,支持AI自动搜索并保存新内容。点击✓标记为已学习,系统会记录你的学习进度。
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
                          quote.is_learned ? (
                            <Tag color="success" icon={<CheckCircleOutlined />}>已学习</Tag>
                          ) : (
                            <Button
                              key="learn"
                              type="link"
                              size="small"
                              icon={<CheckCircleOutlined />}
                              onClick={() => handleMarkAsLearned(quote.id, 'quote')}
                            >
                              标记已学
                            </Button>
                          ),
                          <Button
                            key="edit"
                            type="link"
                            size="small"
                            icon={<EditOutlined />}
                            onClick={() => handleOpenEditModal(quote)}
                          >
                            编辑
                          </Button>,
                          <Popconfirm
                            key="delete"
                            title="确定删除这条名言?"
                            onConfirm={() => handleDelete(quote.id, 'quote')}
                            okText="确定"
                            cancelText="取消"
                          >
                            <Button
                              type="link"
                              size="small"
                              danger
                              icon={<DeleteOutlined />}
                            >
                              删除
                            </Button>
                          </Popconfirm>,
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
                              {quote.score && <Tag color="blue">相似度: {(quote.score * 100).toFixed(0)}%</Tag>}
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
                          {searchTopic ? '未找到相关名言,请尝试其他关键词或AI搜索' : '输入关键词后点击搜索'}
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
                          material.is_learned ? (
                            <Tag color="success" icon={<CheckCircleOutlined />}>已学习</Tag>
                          ) : (
                            <Button
                              key="learn"
                              type="link"
                              size="small"
                              icon={<CheckCircleOutlined />}
                              onClick={() => handleMarkAsLearned(material.id, 'material')}
                            >
                              标记已学
                            </Button>
                          ),
                          <Button
                            key="edit"
                            type="link"
                            size="small"
                            icon={<EditOutlined />}
                            onClick={() => handleOpenEditModal(material)}
                          >
                            编辑
                          </Button>,
                          <Popconfirm
                            key="delete"
                            title="确定删除这个案例?"
                            onConfirm={() => handleDelete(material.id, 'material')}
                            okText="确定"
                            cancelText="取消"
                          >
                            <Button
                              type="link"
                              size="small"
                              danger
                              icon={<DeleteOutlined />}
                            >
                              删除
                            </Button>
                          </Popconfirm>,
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
                              {material.score && <Tag color="blue">相似度: {(material.score * 100).toFixed(0)}%</Tag>}
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
                          {searchTopic ? '未找到相关案例,请尝试其他关键词或AI搜索' : '输入关键词后点击搜索'}
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

      {/* 编辑弹窗 */}
      <Modal
        title={`编辑${activeTab === 'quotes' ? '名言' : '案例'}`}
        open={editModalVisible}
        onOk={handleSaveEdit}
        onCancel={() => {
          setEditModalVisible(false);
          setEditingItem(null);
          editForm.resetFields();
        }}
        okText="保存"
        cancelText="取消"
        width={700}
      >
        <Form
          form={editForm}
          layout="vertical"
          style={{ marginTop: 16 }}
        >
          {activeTab === 'quotes' ? (
            <>
              <Form.Item
                name="content"
                label="名言内容"
                rules={[{ required: true, message: '请输入名言内容' }]}
              >
                <TextArea rows={4} placeholder="输入名言内容" />
              </Form.Item>
              <Form.Item
                name="author"
                label="作者"
                rules={[{ required: true, message: '请输入作者' }]}
              >
                <Input placeholder="输入作者姓名" />
              </Form.Item>
              <Form.Item
                name="source"
                label="出处"
                rules={[{ required: true, message: '请输入出处' }]}
              >
                <Input placeholder="输入出处(如:论语)" />
              </Form.Item>
            </>
          ) : (
            <>
              <Form.Item
                name="title"
                label="案例标题"
                rules={[{ required: true, message: '请输入案例标题' }]}
              >
                <Input placeholder="输入案例标题" />
              </Form.Item>
              <Form.Item
                name="content"
                label="案例内容"
                rules={[{ required: true, message: '请输入案例内容' }]}
              >
                <TextArea rows={6} placeholder="输入案例详细内容" />
              </Form.Item>
              <Form.Item
                name="type"
                label="案例类型"
                rules={[{ required: true, message: '请选择案例类型' }]}
              >
                <Select placeholder="选择案例类型">
                  <Select.Option value="历史事件">历史事件</Select.Option>
                  <Select.Option value="人物故事">人物故事</Select.Option>
                  <Select.Option value="现实案例">现实案例</Select.Option>
                </Select>
              </Form.Item>
            </>
          )}
        </Form>
      </Modal>
    </div>
  );
};

export default QuotesAndMaterialsPage;
