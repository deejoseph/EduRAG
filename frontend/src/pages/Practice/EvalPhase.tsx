import React, { useState } from 'react';
import { Button, Alert, Card, Typography, Descriptions, Tag, Switch, message } from 'antd';
import { TrophyOutlined, ClockCircleOutlined, BookOutlined } from '@ant-design/icons';
import { usePracticeStore } from '../../store/practiceStore';
import { practiceApi } from '../../api/practice';
import { addToPortfolio } from '../../api/portfolio';
import AnswerDisplay from '../../components/writing/AnswerDisplay';
import ReferencePanel from '../../components/writing/ReferencePanel';
import LoadingOverlay from '../../components/common/LoadingOverlay';
import type { Reference } from '../../types/api';

const { Text, Paragraph } = Typography;

const formatTime = (seconds: number) => {
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${m}分${s}秒`;
};

const EvalPhase: React.FC = () => {
  const {
    topic, sessionId, phases, totalElapsed, totalScore,
    includeInLog, setIncludeInLog,
    submitPhase, setTotalScore, setStatus,
  } = usePracticeStore();

  const phase = phases[3];
  const essayPhase = phases[2];
  const [loading, setLoading] = useState(false);
  const [evaluated, setEvaluated] = useState(!!phase?.submitted_at);

  const essayText = essayPhase?.student_content || '';

  // 添加到作品集
  const handleAddToPortfolio = async () => {
    if (!essayText.trim()) {
      message.warning('作文内容为空，无法添加');
      return;
    }
    try {
      await addToPortfolio({
        content: essayText.trim(),
        title: topic.trim().slice(0, 50),
        topic: topic.trim(),
        source: 'practice',
        metadata: {
          session_id: sessionId,
          total_time_seconds: totalElapsed,
        },
        ai_feedback: phase?.ai_feedback || undefined,
        references: (phase?.ai_references as any) || undefined,
        score: totalScore || undefined,
      });
      message.success('已添加到作品集！');
    } catch (error) {
      message.error('添加失败，请重试');
      console.error(error);
    }
  };

  const handleEvaluate = async () => {
    if (!essayText.trim()) {
      message.warning('作文内容为空，无法评估');
      return;
    }
    setLoading(true);
    try {
      const res = await practiceApi.savePhase({
        session_id: sessionId!,
        phase_type: 'evaluation',
        student_content: essayText,
        duration_seconds: 0,
      });
      submitPhase(3, res.ai_feedback || '', res.references || []);

      // 提取总分
      const scoreMatch = res.ai_feedback?.match(/总分[：:]\s*(\d+)/);
      if (scoreMatch) setTotalScore(parseInt(scoreMatch[1]));

      setEvaluated(true);
      setStatus('completed');

      // 同步成长日志开关状态到后端
      practiceApi.toggleLog(sessionId!, includeInLog).catch(() => {});

      message.success('评估报告生成完成');
    } catch {
      // handled
    } finally {
      setLoading(false);
    }
  };

  return (
    <LoadingOverlay loading={loading} text="AI 正在评估你的作文...">
      <Alert message={`题目：${topic}`} type="info" showIcon style={{ marginBottom: 16 }} />

      {/* 作文只读展示 */}
      <Card title="你的作文" size="small" style={{ marginBottom: 16 }}>
        <Paragraph style={{ whiteSpace: 'pre-wrap', lineHeight: 2, fontSize: 15 }}>
          {essayText || '（未提交作文）'}
        </Paragraph>
        <Text type="secondary">{essayText.replace(/\s/g, '').length} 字</Text>
      </Card>

      {!evaluated && (
        <>
          <Card size="small" style={{ marginBottom: 16 }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div>
                <Text strong>计入成长日志</Text>
                <br />
                <Text type="secondary" style={{ fontSize: 12 }}>
                  关闭后本次训练不会记录在成长日志中
                </Text>
              </div>
              <Switch
                checked={includeInLog}
                onChange={(checked) => setIncludeInLog(checked)}
                checkedChildren="计入"
                unCheckedChildren="不计入"
              />
            </div>
          </Card>

          <Button
            type="primary"
            icon={<TrophyOutlined />}
            onClick={handleEvaluate}
            size="large"
            block
          >
            生成 AI 评估报告
          </Button>
        </>
      )}

      {evaluated && (
        <>
          {/* 训练总结 */}
          <Card title="训练总结" size="small" style={{ marginBottom: 16 }}>
            <Descriptions column={{ xs: 1, sm: 2, md: 4 }} size="small">
              <Descriptions.Item label="审题用时">
                <Tag><ClockCircleOutlined /> {formatTime(phases[0]?.duration_seconds || 0)}</Tag>
              </Descriptions.Item>
              <Descriptions.Item label="提纲用时">
                <Tag><ClockCircleOutlined /> {formatTime(phases[1]?.duration_seconds || 0)}</Tag>
              </Descriptions.Item>
              <Descriptions.Item label="写作用时">
                <Tag><ClockCircleOutlined /> {formatTime(phases[2]?.duration_seconds || 0)}</Tag>
              </Descriptions.Item>
              <Descriptions.Item label="总用时">
                <Tag color="blue"><ClockCircleOutlined /> {formatTime(totalElapsed)}</Tag>
              </Descriptions.Item>
            </Descriptions>
            {totalScore !== null && (
              <div style={{ textAlign: 'center', marginTop: 16 }}>
                <Text type="secondary">总分</Text>
                <div style={{ fontSize: 48, fontWeight: 700, color: totalScore >= 50 ? '#52c41a' : '#ff4d4f' }}>
                  {totalScore}
                </div>
                <Text type="secondary">/ 100</Text>
              </div>
            )}
          </Card>

          <AnswerDisplay content={phase?.ai_feedback || null} title="评估报告" />
          <ReferencePanel references={(phase?.ai_references || []) as Reference[]} />

          {/* 添加到作品集按钮 */}
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
        </>
      )}
    </LoadingOverlay>
  );
};

export default EvalPhase;
