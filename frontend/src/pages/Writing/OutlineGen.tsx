import React, { useState } from 'react';
import { Form, Input, Select, Button, message, Alert } from 'antd';
import { FileTextOutlined } from '@ant-design/icons';
import { useWritingStore } from '../../store/writingStore';
import { writingApi } from '../../api/writing';
import { WRITING_STYLES, WORD_COUNTS } from '../../constants';
import AnswerDisplay from '../../components/writing/AnswerDisplay';
import ReferencePanel from '../../components/writing/ReferencePanel';
import LoadingOverlay from '../../components/common/LoadingOverlay';

const OutlineGen: React.FC = () => {
  const {
    topic, thesis, setThesis, style, setStyle, wordCount, setWordCount,
    outlineResult, setOutlineResult, outlineRefs, setOutlineRefs,
  } = useWritingStore();

  const [loading, setLoading] = useState(false);

  if (!topic) {
    return (
      <Alert
        message="请先完成审题分析"
        description="请返回上一步输入作文题目并进行审题分析。"
        type="info"
        showIcon
      />
    );
  }

  const handleSubmit = async () => {
    setLoading(true);
    try {
      const res = await writingApi.outline({
        topic: topic.trim(),
        thesis: thesis.trim() || undefined,
        style,
        word_count: wordCount,
      });
      setOutlineResult(res.answer);
      setOutlineRefs(res.references);
      message.success('构思提纲生成完成');
    } catch (e) {
      // error handled by interceptor
    } finally {
      setLoading(false);
    }
  };

  return (
    <LoadingOverlay loading={loading}>
      <Alert
        message={`当前题目：${topic}`}
        type="info"
        showIcon
        style={{ marginBottom: 16 }}
      />

      <Form layout="vertical">
        <Form.Item label="立意方向（可选，不填则由 AI 自行推荐）">
          <Input.TextArea
            value={thesis}
            onChange={(e) => setThesis(e.target.value)}
            placeholder="例如：以「坚持」为核心，从个人成长角度立意..."
            rows={2}
          />
        </Form.Item>

        <Form.Item label="文体" style={{ display: 'inline-block', width: 'calc(33% - 8px)', marginRight: 12 }}>
          <Select
            value={style}
            onChange={setStyle}
            options={WRITING_STYLES.map(s => ({ label: s.label, value: s.value }))}
          />
        </Form.Item>

        <Form.Item label="目标字数" style={{ display: 'inline-block', width: 'calc(33% - 8px)' }}>
          <Select
            value={wordCount}
            onChange={setWordCount}
            options={WORD_COUNTS.map(w => ({ label: w.label, value: w.value }))}
          />
        </Form.Item>

        <Button
          type="primary"
          icon={<FileTextOutlined />}
          onClick={handleSubmit}
          size="large"
          block
          style={{ marginTop: 8 }}
        >
          生成构思提纲
        </Button>
      </Form>

      <AnswerDisplay content={outlineResult} title="构思提纲" />
      <ReferencePanel references={outlineRefs} />
    </LoadingOverlay>
  );
};

export default OutlineGen;
