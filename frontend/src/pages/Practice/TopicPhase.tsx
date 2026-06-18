import React, { useState, useEffect } from 'react';
import { Input, Button, Alert, Card, Tag, message } from 'antd';
import { ClockCircleOutlined, SendOutlined } from '@ant-design/icons';
import { usePracticeStore } from '../../store/practiceStore';
import { practiceApi } from '../../api/practice';
import AnswerDisplay from '../../components/writing/AnswerDisplay';
import LoadingOverlay from '../../components/common/LoadingOverlay';

const TopicPhase: React.FC = () => {
  const {
    topic, topicType, gradeLevel, sessionId,
    phases, phaseElapsed, timerRunning, setStudentContent,
    submitPhase, startPhaseTimer,
  } = usePracticeStore();

  const phase = phases[0];
  const suggestedMin = Math.round((phase?.suggested_seconds || 600) / 60);
  const [content, setContent] = useState(phase?.student_content || '');
  const [loading, setLoading] = useState(false);
  const [submitted, setSubmitted] = useState(!!phase?.submitted_at);

  // 启动正计时
  useEffect(() => {
    if (phase && !phase.submitted_at && !timerRunning && phaseElapsed === 0) {
      startPhaseTimer();
    }
  }, []);

  // 同步 store 内容
  useEffect(() => {
    if (phase?.student_content !== undefined) {
      setContent(phase.student_content);
    }
  }, [phase?.student_content]);

  const handleSubmit = async () => {
    if (!content.trim()) {
      message.warning('请先写出你的审题分析');
      return;
    }
    setLoading(true);
    try {
      const res = await practiceApi.savePhase({
        session_id: sessionId!,
        phase_type: 'topic_analysis',
        student_content: content.trim(),
        duration_seconds: phaseElapsed,
      });
      submitPhase(0, res.ai_feedback || '', res.references || []);
      setSubmitted(true);
      message.success('审题分析已提交');
    } catch {
      // handled by interceptor
    } finally {
      setLoading(false);
    }
  };

  const minutes = Math.floor(phaseElapsed / 60);
  const seconds = phaseElapsed % 60;
  const overSuggested = phase?.suggested_seconds > 0 && phaseElapsed > phase.suggested_seconds;

  return (
    <LoadingOverlay loading={loading} text="AI 正在对比分析你的审题...">
      <Alert
        message={`题目：${topic}`}
        description={`题型：${topicType} | 学段：${gradeLevel}`}
        type="info"
        showIcon
        style={{ marginBottom: 16 }}
      />

      <Card
        title="阶段 1：审题分析"
        extra={
          !submitted && (
            <Tag icon={<ClockCircleOutlined />} color="processing" style={{ fontSize: 14, padding: '4px 12px' }}>
              已用 {String(minutes).padStart(2, '0')}:{String(seconds).padStart(2, '0')}
            </Tag>
          )
        }
        size="small"
      >
        <p style={{ color: '#666', marginBottom: 12 }}>
          请根据题目写出你的审题分析：包括立意方向、关键词、写作思路等。建议用时 {suggestedMin} 分钟。
        </p>

        {overSuggested && !submitted && (
          <Alert
            message="已超过建议用时，请按自己的节奏完成"
            type="info"
            showIcon
            style={{ marginBottom: 12 }}
          />
        )}

        <Input.TextArea
          value={content}
          onChange={(e) => {
            setContent(e.target.value);
            setStudentContent(0, e.target.value);
          }}
          placeholder="写出你对题目的理解、关键词提取、可能的立意方向..."
          rows={10}
          disabled={submitted}
          style={{ fontSize: 15, lineHeight: 1.8 }}
        />

        {!submitted && (
          <Button
            type="primary"
            icon={<SendOutlined />}
            onClick={handleSubmit}
            style={{ marginTop: 12 }}
            block
            size="large"
          >
            提交审题分析
          </Button>
        )}
      </Card>

      {submitted && (
        <AnswerDisplay content={phase?.ai_feedback || null} title="AI 对比分析" />
      )}
    </LoadingOverlay>
  );
};

export default TopicPhase;
