import React, { useState } from 'react';
import { Form, Input, Select, Button, message } from 'antd';
import { BulbOutlined } from '@ant-design/icons';
import { useWritingStore } from '../../store/writingStore';
import { writingApi } from '../../api/writing';
import { TOPIC_TYPES, GRADE_LEVELS } from '../../constants';
import AnswerDisplay from '../../components/writing/AnswerDisplay';
import ReferencePanel from '../../components/writing/ReferencePanel';
import LoadingOverlay from '../../components/common/LoadingOverlay';

const TopicAnalysis: React.FC = () => {
  const {
    topic, setTopic, topicType, setTopicType, gradeLevel, setGradeLevel,
    analysisResult, setAnalysisResult, analysisRefs, setAnalysisRefs,
  } = useWritingStore();

  const [loading, setLoading] = useState(false);

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

  return (
    <LoadingOverlay loading={loading}>
      <Form layout="vertical">
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

        <Button
          type="primary"
          icon={<BulbOutlined />}
          onClick={handleSubmit}
          size="large"
          block
        >
          开始审题分析
        </Button>
      </Form>

      <AnswerDisplay content={analysisResult} title="审题分析结果" />
      <ReferencePanel references={analysisRefs} />
    </LoadingOverlay>
  );
};

export default TopicAnalysis;
