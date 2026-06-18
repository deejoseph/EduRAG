import React, { useState } from 'react';
import { Form, Input, Select, Checkbox, Button, message, Alert } from 'antd';
import { TrophyOutlined, BookOutlined } from '@ant-design/icons';
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

const EssayEval: React.FC = () => {
  const {
    topic, currentEssay, gradeLevel, setGradeLevel,
    evaluationResult, setEvaluationResult,
    evaluationRefs, setEvaluationRefs,
  } = useWritingStore();

  const [essay, setEssay] = useState(currentEssay || '');
  const [rubric, setRubric] = useState<string[]>(DEFAULT_SCORING_RUBRIC as unknown as string[]);
  const [loading, setLoading] = useState(false);

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
        evaluation_scores: evaluationResult ? extractDimensionScores(evaluationResult) : undefined,
      });
      message.success('已添加到作品集！');
    } catch (error) {
      message.error('添加失败，请重试');
      console.error(error);
    }
  };

  // 从评估文本中提取分数（简单解析）
  const extractScore = (text: string): number | undefined => {
    const match = text.match(/总分[：:]\s*(\d+)/);
    return match ? parseInt(match[1]) : undefined;
  };

  const extractDimensionScores = (_text: string) => {
    // 这里可以根据实际 AI 返回格式进行解析
    // 暂时返回 undefined，后续可以完善
    return undefined;
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

        <Button
          type="primary"
          icon={<TrophyOutlined />}
          onClick={handleSubmit}
          size="large"
          block
        >
          生成评估报告
        </Button>
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
          >
            添加到作品集
          </Button>
        </div>
      )}
    </LoadingOverlay>
  );
};

export default EssayEval;
