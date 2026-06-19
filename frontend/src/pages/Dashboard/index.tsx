import React, { useEffect, useState } from 'react';
import { Card, Row, Col, Statistic, Button, Table, Tag, Alert, Select, Space, Typography, Modal, Input, message } from 'antd';
import {
  DatabaseOutlined,
  EditOutlined,
  SearchOutlined,
  ApiOutlined,
  ThunderboltOutlined,
  BookOutlined,
  PlusOutlined,
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { healthApi, searchApi } from '../../api/search';
import type { StatsResponse, CollectionsResponse, HealthResponse } from '../../types/api';

const { Text } = Typography;

// 学科定义
interface Subject {
  id: string;
  name: string;
  icon: string;
  description: string;
  collection?: string;
  isCustom?: boolean;
}

// 默认学科列表
const DEFAULT_SUBJECTS: Subject[] = [
  {
    id: 'chinese_writing',
    name: '中文写作',
    icon: '📝',
    description: '高考语文作文训练',
    collection: 'chinese_essays',
  },
];

const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [stats, setStats] = useState<StatsResponse | null>(null);
  const [collections, setCollections] = useState<CollectionsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // 学科选择状态
  const [currentSubject, setCurrentSubject] = useState<string>('chinese_writing');
  const [availableSubjects, setAvailableSubjects] = useState<Subject[]>(DEFAULT_SUBJECTS);
  
  // 自定义学科弹窗
  const [customSubjectModalVisible, setCustomSubjectModalVisible] = useState(false);
  const [newSubjectName, setNewSubjectName] = useState('');
  const [newSubjectIcon, setNewSubjectIcon] = useState('📚');
  const [newSubjectDescription, setNewSubjectDescription] = useState('');

  // 从localStorage加载自定义学科和选择
  useEffect(() => {
    const savedSubjects = localStorage.getItem('custom_subjects');
    const savedSubject = localStorage.getItem('current_subject');
    
    if (savedSubjects) {
      try {
        const customSubjects = JSON.parse(savedSubjects);
        setAvailableSubjects([...DEFAULT_SUBJECTS, ...customSubjects]);
      } catch (e) {
        console.error('加载自定义学科失败:', e);
      }
    }
    
    if (savedSubject && availableSubjects.find(s => s.id === savedSubject)) {
      setCurrentSubject(savedSubject);
    }
  }, []);

  // 保存学科选择到localStorage
  const handleSubjectChange = (subjectId: string) => {
    setCurrentSubject(subjectId);
    localStorage.setItem('current_subject', subjectId);
  };

  // 添加自定义学科
  const handleAddCustomSubject = () => {
    if (!newSubjectName.trim()) {
      message.warning('请输入学科名称');
      return;
    }

    const newSubject: Subject = {
      id: `custom_${Date.now()}`,
      name: newSubjectName.trim(),
      icon: newSubjectIcon || '📚',
      description: newSubjectDescription.trim() || '自定义学科（即将上线）',
      isCustom: true,
    };

    const updatedSubjects = [...availableSubjects, newSubject];
    setAvailableSubjects(updatedSubjects);
    
    // 保存到localStorage
    const customSubjects = updatedSubjects.filter(s => s.isCustom);
    localStorage.setItem('custom_subjects', JSON.stringify(customSubjects));
    
    message.success(`已添加学科：${newSubject.name}`);
    setCustomSubjectModalVisible(false);
    setNewSubjectName('');
    setNewSubjectIcon('📚');
    setNewSubjectDescription('');
  };

  // 删除自定义学科
  const handleDeleteCustomSubject = (subjectId: string) => {
    const subject = availableSubjects.find(s => s.id === subjectId);
    if (!subject || !subject.isCustom) {
      message.error('只能删除自定义学科');
      return;
    }

    Modal.confirm({
      title: '确认删除',
      content: `确定要删除学科"${subject.name}"吗？`,
      onOk: () => {
        const updatedSubjects = availableSubjects.filter(s => s.id !== subjectId);
        setAvailableSubjects(updatedSubjects);
        
        // 更新localStorage
        const customSubjects = updatedSubjects.filter(s => s.isCustom);
        localStorage.setItem('custom_subjects', JSON.stringify(customSubjects));
        
        // 如果删除的是当前选中的学科，切换回中文写作
        if (currentSubject === subjectId) {
          handleSubjectChange('chinese_writing');
        }
        
        message.success('已删除学科');
      },
    });
  };

  const currentSubjectInfo = availableSubjects.find(s => s.id === currentSubject) || DEFAULT_SUBJECTS[0];

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
      <Space direction="vertical" size="middle" style={{ width: '100%', marginBottom: 24 }}>
        <h2 style={{ margin: 0 }}>EduRAG 智能学习助手</h2>
        
        {/* 学科选择器 */}
        <Card size="small" style={{ background: '#fafafa' }}>
          <Space wrap size="middle" style={{ width: '100%', justifyContent: 'space-between' }}>
            <Space wrap size="middle">
              <Text strong>当前学科：</Text>
              <Select
                value={currentSubject}
                onChange={handleSubjectChange}
                style={{ width: 200 }}
                options={availableSubjects.map(s => ({
                  label: `${s.icon} ${s.name}`,
                  value: s.id,
                }))}
              />
              <Tag color="blue">{currentSubjectInfo.icon} {currentSubjectInfo.name}</Tag>
              <Text type="secondary">{currentSubjectInfo.description}</Text>
            </Space>
            <Button
              type="dashed"
              icon={<PlusOutlined />}
              onClick={() => setCustomSubjectModalVisible(true)}
              size="small"
            >
              自定义学科
            </Button>
          </Space>
        </Card>
      </Space>

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
              disabled={currentSubject !== 'chinese_writing'}
            >
              {currentSubject === 'chinese_writing' ? '开始引导练习' : '该学科暂未开放'}
            </Button>
            <p style={{ marginTop: 8, color: '#666', textAlign: 'center' }}>
              {currentSubject === 'chinese_writing' 
                ? '审题 → 构思 → 引导练习 → 作文评估' 
                : `${currentSubjectInfo.name}的知识检索功能即将上线`}
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
              disabled={currentSubject !== 'chinese_writing'}
            >
              {currentSubject === 'chinese_writing' ? '知识库检索' : '该学科暂未开放'}
            </Button>
            <p style={{ marginTop: 8, color: '#666', textAlign: 'center' }}>
              {currentSubject === 'chinese_writing' 
                ? '搜索范文、素材、真题' 
                : `${currentSubjectInfo.name}的知识库即将上线`}
            </p>
          </Card>
        </Col>
      </Row>

      <Card 
        title={
          <Space>
            <BookOutlined />
            <span>数据集合</span>
            {currentSubjectInfo.collection && (
              <Tag color="processing">{currentSubjectInfo.name}</Tag>
            )}
          </Space>
        } 
        style={{ marginTop: 24 }} 
        loading={loading}
      >
        {currentSubject !== 'chinese_writing' ? (
          <Alert
            message={`${currentSubjectInfo.name}的知识库即将上线`}
            description="我们正在为该学科准备丰富的学习资源，敬请期待！"
            type="info"
            showIcon
          />
        ) : (
          <Table
            dataSource={collections?.collections || []}
            columns={collectionColumns}
            rowKey="name"
            pagination={false}
            size="small"
          />
        )}
      </Card>

      {/* 自定义学科弹窗 */}
      <Modal
        title="自定义学科"
        open={customSubjectModalVisible}
        onOk={handleAddCustomSubject}
        onCancel={() => {
          setCustomSubjectModalVisible(false);
          setNewSubjectName('');
          setNewSubjectIcon('📚');
          setNewSubjectDescription('');
        }}
        okText="添加"
        cancelText="取消"
      >
        <Space direction="vertical" size="middle" style={{ width: '100%' }}>
          <div>
            <Text strong>学科图标：</Text>
            <Input
              value={newSubjectIcon}
              onChange={(e) => setNewSubjectIcon(e.target.value)}
              placeholder="输入emoji图标，如：📚"
              style={{ width: 100, marginTop: 8 }}
            />
          </div>
          <div>
            <Text strong>学科名称：</Text>
            <Input
              value={newSubjectName}
              onChange={(e) => setNewSubjectName(e.target.value)}
              placeholder="例如：计算机科学"
              style={{ marginTop: 8 }}
            />
          </div>
          <div>
            <Text strong>学科描述：</Text>
            <Input.TextArea
              value={newSubjectDescription}
              onChange={(e) => setNewSubjectDescription(e.target.value)}
              placeholder="简要描述该学科的学习内容"
              rows={2}
              style={{ marginTop: 8 }}
            />
          </div>
          <Alert
            message="提示"
            description="新添加的学科目前仅作为占位符，知识检索功能将在后续版本中开发。"
            type="info"
            showIcon
          />
        </Space>
      </Modal>

      {/* 已添加的自定义学科列表 */}
      {availableSubjects.length > DEFAULT_SUBJECTS.length && (
        <Card title="已添加的学科" style={{ marginTop: 24 }} size="small">
          <Space wrap>
            {availableSubjects
              .filter(s => s.isCustom)
              .map(subject => (
                <Tag
                  key={subject.id}
                  color="purple"
                  closable
                  onClose={() => handleDeleteCustomSubject(subject.id)}
                  style={{ cursor: 'pointer' }}
                >
                  {subject.icon} {subject.name}
                </Tag>
              ))}
          </Space>
        </Card>
      )}
    </div>
  );
};

export default Dashboard;
