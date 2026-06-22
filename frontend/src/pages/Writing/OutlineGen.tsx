import React, { useState } from 'react';
import { Form, Input, Select, Button, message, Alert, Card, Space, Typography, Radio } from 'antd';
import { FileTextOutlined, SoundOutlined, StarOutlined } from '@ant-design/icons';
import { useWritingStore } from '../../store/writingStore';
import { writingApi } from '../../api/writing';
import { WRITING_STYLES, WORD_COUNTS } from '../../constants';
import AnswerDisplay from '../../components/writing/AnswerDisplay';
import ReferencePanel from '../../components/writing/ReferencePanel';
import LoadingOverlay from '../../components/common/LoadingOverlay';
import MultiAiResults from '../../components/writing/MultiAiResults';

const { Text } = Typography;

const OutlineGen: React.FC = () => {
  const {
    topic, thesis, setThesis, style, setStyle, wordCount, setWordCount,
    outlineResult, setOutlineResult, outlineRefs, setOutlineRefs,
  } = useWritingStore();

  const [loading, setLoading] = useState(false);

  // 多AI生成相关状态
  const [multiAiMode, setMultiAiMode] = useState(false);
  const [multiAiResults, setMultiAiResults] = useState<any[]>([]);
  const [multiAiLoading, setMultiAiLoading] = useState(false);

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

  // 多AI并行生成播客素材
  const handleMultiAiGenerate = async () => {
    if (!topic.trim()) {
      message.warning('请先完成审题分析');
      return;
    }
    setMultiAiLoading(true);
    try {
      const res = await writingApi.multiAiAnalyze({
        topic: topic.trim(),
        grade_level: '高三',
        topic_type: '材料作文',
        models: ['qwen3:8b', 'gemma3:4b'],
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
      <Alert
        message={`当前题目：${topic}`}
        type="info"
        showIcon
        style={{ marginBottom: 16 }}
      />

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

        {multiAiMode ? (
          <Button
            type="primary"
            icon={<SoundOutlined />}
            onClick={handleMultiAiGenerate}
            size="large"
            block
            loading={multiAiLoading}
            style={{ marginTop: 8, background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }}
          >
            一键生成播客素材（多AI并行）
          </Button>
        ) : (
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
        )}
      </Form>

      {/* 多AI结果展示 */}
      {multiAiMode && multiAiResults.length > 0 && (
        <div style={{ marginTop: 24 }}>
          <MultiAiResults
            results={multiAiResults}
            stage="outline"
            topic={topic}
            loading={multiAiLoading}
            onRegenerate={handleMultiAiGenerate}
          />
        </div>
      )}

      {/* 普通模式结果展示 */}
      {!multiAiMode && (
        <>
          <AnswerDisplay content={outlineResult} title="构思提纲" />
          <ReferencePanel references={outlineRefs} />
        </>
      )}
    </LoadingOverlay>
  );
};

export default OutlineGen;
