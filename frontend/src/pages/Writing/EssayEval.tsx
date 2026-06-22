import React, { useState } from 'react';
import { Form, Input, Select, Checkbox, Button, message, Alert, Card, Space, Typography, Radio } from 'antd';
import { TrophyOutlined, BookOutlined, SoundOutlined } from '@ant-design/icons';
import MultiAiResults from '../../components/writing/MultiAiResults';
import { useWritingStore } from '../../store/writingStore';
import { writingApi } from '../../api/writing';
import { addToPortfolio } from '../../api/portfolio';
import {
  GRADE_LEVELS,
  SCORING_RUBRIC_OPTIONS, DEFAULT_SCORING_RUBRIC,
} from '../../constants';
import AnswerDisplay from '../../components/writing/AnswerDisplay';
import ReferencePanel from '../../components/writing/ReferencePanel';
import LoadingOverlay from '../../components/common/LoadingOverlay';

const { Text } = Typography;

const EssayEval: React.FC = () => {
  const {
    topic, currentEssay, gradeLevel, setGradeLevel,
    evaluationResult, setEvaluationResult,
    evaluationRefs, setEvaluationRefs,
  } = useWritingStore();

  const [essay, setEssay] = useState(currentEssay || '');
  const [rubric, setRubric] = useState<string[]>(DEFAULT_SCORING_RUBRIC as unknown as string[]);
  const [loading, setLoading] = useState(false);
  
  // 多AI生成相关状态
  const [multiAiMode, setMultiAiMode] = useState(false); // 是否启用多AI模式
  const [multiAiResults, setMultiAiResults] = useState<any[]>([]);
  const [multiAiLoading, setMultiAiLoading] = useState(false);

  if (!topic) {
    return (
      <Alert
        message="请先完成审题分析"
        description="请返回第一步输入作文题目。"
        type="info"
        showIcon
      />
    );
  }

  const handleSubmit = async () => {
    if (!essay.trim()) {
      message.warning('请输入作文内容');
      return;
    }
    setLoading(true);
    try {
      const res = await writingApi.evaluate({
        essay: essay.trim(),
        topic: topic.trim(),
        grade_level: gradeLevel,
        scoring_rubric: rubric,
      });
      setEvaluationResult(res.answer);
      setEvaluationRefs(res.references);
      message.success('评估报告生成完成');
    } catch (e) {
      // error handled by interceptor
    } finally {
      setLoading(false);
    }
  };

  // 添加到作品集
  const handleAddToPortfolio = async () => {
    if (!essay.trim()) {
      message.warning('请先输入作文内容');
      return;
    }
    try {
      await addToPortfolio({
        content: essay.trim(),
        title: topic.trim().slice(0, 50),
        topic: topic.trim(),
        source: 'writing',
        metadata: {
          grade_level: gradeLevel,
          scoring_rubric: rubric,
        },
        ai_feedback: evaluationResult || undefined,
        references: evaluationRefs || undefined,
        score: evaluationResult ? extractScore(evaluationResult) : undefined,
      });
      message.success('✅ 已添加到作品集');
    } catch (error) {
      console.error('添加失败:', error);
    }
  };

  // 导出到播客模块
  const handleExportToPodcast = async () => {
    if (!evaluationResult) {
      message.warning('请先生成评估报告');
      return;
    }
    
    try {
      const response = await writingApi.exportToPodcast({
        stage: 'evaluation',
        topic: topic || '未知题目',
        content: evaluationResult,
        ai_model: 'qwen3:8b',
      });
      message.success(`✅ 已导出到播客模块：${response.material_id}`);
    } catch (error) {
      console.error('导出失败:', error);
      message.error('导出失败');
    }
  };

  // 多AI并行生成播客素材
  const handleMultiAiGenerate = async () => {
    if (!essay.trim()) {
      message.warning('请先输入作文内容');
      return;
    }
    
    setMultiAiLoading(true);
    try {
      const res = await writingApi.multiAiAnalyze({
        topic: essay.trim().slice(0, 100), // 使用作文前100字作为topic
        grade_level: gradeLevel,
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
      message.error('生成失败，请检查连接');
    } finally {
      setMultiAiLoading(false);
    }
  };

  // 从评估文本中提取分数（简单解析）
  const extractScore = (text: string): number | undefined => {
    const match = text.match(/总分[：:]\s*(\d+)/);
    return match ? parseInt(match[1]) : undefined;
  };

  return (
    <LoadingOverlay loading={loading}>
      <Alert
        message={`当前题目：${topic}`}
        type="info"
        showIcon
        style={{ marginBottom: 16 }}
      />

      {/* 播客素材模式选项卡 */}
      <Card size="small" style={{ marginBottom: 16 }}>
        <Space>
          <span style={{ fontWeight: 500 }}>生成模式：</span>
          <Radio.Group
            value={multiAiMode}
            onChange={(e) => setMultiAiMode(e.target.value)}
            buttonStyle="solid"
          >
            <Radio.Button value={false}>
              <TrophyOutlined /> 普通评估
            </Radio.Button>
            <Radio.Button value={true}>
              <SoundOutlined /> 播客素材模式（多AI）
            </Radio.Button>
          </Radio.Group>
        </Space>
      </Card>

      <Form layout="vertical">
        <Form.Item label="作文全文" required>
          <Input.TextArea
            value={essay}
            onChange={(e) => setEssay(e.target.value)}
            placeholder="粘贴或输入你的作文全文..."
            rows={10}
            className="essay-editor"
          />
        </Form.Item>

        <Form.Item label="年级" style={{ display: 'inline-block', width: 'calc(50% - 8px)', marginRight: 16 }}>
          <Select
            value={gradeLevel}
            onChange={setGradeLevel}
            options={GRADE_LEVELS.map(g => ({ label: g.label, value: g.value }))}
          />
        </Form.Item>

        <Form.Item label="评分维度" style={{ display: 'inline-block', width: 'calc(50% - 8px)' }}>
          <Checkbox.Group
            options={SCORING_RUBRIC_OPTIONS.map(s => ({ label: s.label, value: s.value }))}
            value={rubric}
            onChange={(vals) => setRubric(vals as string[])}
          />
        </Form.Item>

        {multiAiMode ? (
          <Button
            type="primary"
            icon={<SoundOutlined />}
            onClick={handleMultiAiGenerate}
            loading={multiAiLoading}
            size="large"
            block
            style={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }}
          >
            一键生成播客素材（多AI并行）
          </Button>
        ) : (
          <Button
            type="primary"
            icon={<TrophyOutlined />}
            onClick={handleSubmit}
            size="large"
            block
          >
            生成评估报告
          </Button>
        )}
      </Form>

      <AnswerDisplay content={evaluationResult} title="评估报告" />
      <ReferencePanel references={evaluationRefs} />

      {/* 添加到作品集按钮 */}
      {evaluationResult && (
        <div style={{ marginTop: 16 }}>
          <Button
            type="default"
            icon={<BookOutlined />}
            onClick={handleAddToPortfolio}
            block
            size="large"
            style={{ marginBottom: 12 }}
          >
            添加到作品集
          </Button>
          
          {/* 导出到播客 */}
          <Card size="small">
            <Space direction="vertical" style={{ width: '100%' }}>
              <Text strong>🎙️ 播客素材生成</Text>
              <Text type="secondary" style={{ fontSize: 12 }}>
                将AI评估报告转换为播客文案，方便后续生成语音复习
              </Text>
              <Button
                icon={<SoundOutlined />}
                onClick={handleExportToPodcast}
                disabled={!evaluationResult}
              >
                生成播客素材
              </Button>
            </Space>
          </Card>
        </div>
      )}

      {/* 多AI结果展示 */}
      {multiAiMode && multiAiResults.length > 0 && (
        <div style={{ marginTop: 24 }}>
          <MultiAiResults
            results={multiAiResults}
            stage="evaluation"
            topic={essay.slice(0, 50)}
            loading={multiAiLoading}
            onRegenerate={handleMultiAiGenerate}
          />
        </div>
      )}
    </LoadingOverlay>
  );
};

export default EssayEval;
