import React, { useState, useEffect } from 'react';
import { Form, Input, Select, Button, message, Card, Badge, Space, Typography, Tag, Radio } from 'antd';
import { BulbOutlined, BookOutlined, SoundOutlined, StarOutlined } from '@ant-design/icons';
import { useWritingStore } from '../../store/writingStore';
import { writingApi } from '../../api/writing';
import { getFavorites } from '../../api/hotTopics';
import { TOPIC_TYPES, GRADE_LEVELS } from '../../constants';
import AnswerDisplay from '../../components/writing/AnswerDisplay';
import ReferencePanel from '../../components/writing/ReferencePanel';
import LoadingOverlay from '../../components/common/LoadingOverlay';
import MultiAiResults from '../../components/writing/MultiAiResults';

const { Text } = Typography;

const TopicAnalysis: React.FC = () => {
  const {
    topic, setTopic, topicType, setTopicType, gradeLevel, setGradeLevel,
    analysisResult, setAnalysisResult, analysisRefs, setAnalysisRefs,
  } = useWritingStore();

  const [loading, setLoading] = useState(false);
  const [favoritesLoading, setFavoritesLoading] = useState(false);
  const [favorites, setFavorites] = useState<any[]>([]);
  
  // 多AI生成相关状态
  const [multiAiMode, setMultiAiMode] = useState(false); // 是否启用多AI模式
  const [multiAiResults, setMultiAiResults] = useState<any[]>([]);
  const [multiAiLoading, setMultiAiLoading] = useState(false);
  
  // 加载题库列表
  useEffect(() => {
    loadFavorites();
  }, []);
  
  const loadFavorites = async () => {
    setFavoritesLoading(true);
    try {
      const res = await getFavorites('practice_count');
      setFavorites(res.topics);
    } catch (error) {
      console.error('加载题库失败:', error);
    } finally {
      setFavoritesLoading(false);
    }
  };
  
  // 选择题目
  const handleSelectTopic = (topicData: any) => {
    setTopic(topicData.essay_prompt || topicData.title);
    message.success(`已选择题目：${topicData.title}`);
  };

  // 普通审题分析
  const handleSubmit = async () => {
    if (!topic.trim()) {
      message.warning('请输入作文题目');
      return;
    }
    setLoading(true);
    try {
      const res = await writingApi.analyze({
        topic: topic.trim(),
        topic_type: topicType,
        grade_level: gradeLevel,
      });
      setAnalysisResult(res.answer);
      setAnalysisRefs(res.references);
      message.success('审题分析完成');
    } catch (e) {
      // error handled by interceptor
    } finally {
      setLoading(false);
    }
  };

  // 多AI并行生成播客素材
  const handleMultiAiGenerate = async () => {
    if (!topic.trim()) {
      message.warning('请输入作文题目');
      return;
    }
    
    setMultiAiLoading(true);
    try {
      const res = await writingApi.multiAiAnalyze({
        topic: topic.trim(),
        grade_level: gradeLevel,
        topic_type: topicType,
        models: ['qwen3:8b', 'gemma3:4b'], // 使用2个差异化模型
      });
      
      if (res.success && res.results) {
        setMultiAiResults(res.results);
        message.success(`✅ 多AI生成完成！共 ${res.count} 个结果`);
      } else {
        message.error('生成失败，请重试');
      }
    } catch (error) {
      console.error('多AI生成失败:', error);
      message.error('生成失败，请检查网络连接');
    } finally {
      setMultiAiLoading(false);
    }
  };

  return (
    <LoadingOverlay loading={loading}>
      {/* 从题库选择 */}
      <Card 
        title={
          <Space>
            <BookOutlined />
            <span>从题库选择题目</span>
            {favorites.length > 0 && (
              <Badge count={favorites.length} overflowCount={99999} style={{ backgroundColor: '#52c41a' }} />
            )}
          </Space>
        }
        size="small"
        style={{ marginBottom: 24 }}
        loading={favoritesLoading}
      >
        {favorites.length === 0 ? (
          <Text type="secondary">暂无收藏的题目，请先到"命题热点"或"知识检索"页面收藏感兴趣的话题</Text>
        ) : (
          <Select
            placeholder="选择要练习的题目..."
            style={{ width: '100%' }}
            onChange={(value) => {
              const selected = favorites.find(f => f.title === value);
              if (selected) handleSelectTopic(selected);
            }}
            options={favorites.map(f => ({
              label: (
                <Space direction="vertical" size={0}>
                  <Space size={4} align="center">
                    <Text strong>{f.title}</Text>
                    {f.source === 'rag' && (
                      <Tag color="green" style={{ fontSize: 10, lineHeight: '16px', padding: '0 4px' }}>
                        RAG
                      </Tag>
                    )}
                  </Space>
                  <Space size="small">
                    <Badge count={`已练习${f.practice_count || 0}次`} style={{ backgroundColor: f.practice_count > 0 ? '#faad14' : '#d9d9d9' }} />
                    <Text type="secondary" style={{ fontSize: 12 }}>{f.category}</Text>
                  </Space>
                </Space>
              ),
              value: f.title,
            }))}
          />
        )}
      </Card>
      
      <Form layout="vertical">
        {/* 模式切换 */}
        <Card size="small" style={{ marginBottom: 16, background: '#f0f5ff', border: '1px solid #adc6ff' }}>
          <Space>
            <StarOutlined style={{ color: '#1890ff' }} />
            <Text strong>生成模式：</Text>
            <Radio.Group
              value={multiAiMode}
              onChange={(e) => setMultiAiMode(e.target.value)}
              buttonStyle="solid"
            >
              <Radio.Button value={false}>普通模式</Radio.Button>
              <Radio.Button value={true}>
                <SoundOutlined /> 播客素材模式（多AI）
              </Radio.Button>
            </Radio.Group>
          </Space>
        </Card>

        <Form.Item label="作文题目" required>
          <Input.TextArea
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            placeholder="请输入作文题目或材料内容..."
            rows={4}
            style={{ fontSize: 16 }}
          />
        </Form.Item>

        <Form.Item label="题目类型" style={{ display: 'inline-block', width: 'calc(50% - 8px)', marginRight: 16 }}>
          <Select
            value={topicType}
            onChange={setTopicType}
            options={TOPIC_TYPES.map(t => ({ label: t.label, value: t.value }))}
          />
        </Form.Item>

        <Form.Item label="年级" style={{ display: 'inline-block', width: 'calc(50% - 8px)' }}>
          <Select
            value={gradeLevel}
            onChange={setGradeLevel}
            options={GRADE_LEVELS.map(g => ({ label: g.label, value: g.value }))}
          />
        </Form.Item>

        {multiAiMode ? (
          <Button
            type="primary"
            icon={<SoundOutlined />}
            onClick={handleMultiAiGenerate}
            size="large"
            block
            loading={multiAiLoading}
            style={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }}
          >
            一键生成播客素材（多AI并行）
          </Button>
        ) : (
          <Button
            type="primary"
            icon={<BulbOutlined />}
            onClick={handleSubmit}
            size="large"
            block
          >
            开始审题分析
          </Button>
        )}
      </Form>

      {/* 多AI结果展示 */}
      {multiAiMode && multiAiResults.length > 0 && (
        <div style={{ marginTop: 24 }}>
          <MultiAiResults
            results={multiAiResults}
            stage="analysis"
            topic={topic}
            loading={multiAiLoading}
            onRegenerate={handleMultiAiGenerate}
          />
        </div>
      )}

      {/* 普通模式结果展示 */}
      {!multiAiMode && (
        <>
          <AnswerDisplay content={analysisResult} title="审题分析结果" />
          <ReferencePanel references={analysisRefs} />
        </>
      )}
    </LoadingOverlay>
  );
};

export default TopicAnalysis;
