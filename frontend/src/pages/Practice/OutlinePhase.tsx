import React, { useState, useEffect } from 'react';
import { Input, Button, Alert, Card, Collapse, Tag, message } from 'antd';
import { ClockCircleOutlined, SendOutlined } from '@ant-design/icons';
import { usePracticeStore } from '../../store/practiceStore';
import { practiceApi } from '../../api/practice';
import AnswerDisplay from '../../components/writing/AnswerDisplay';
import LoadingOverlay from '../../components/common/LoadingOverlay';

const OutlinePhase: React.FC = () => {
  const {
    topic, sessionId, phases, phaseElapsed, timerRunning,
    setStudentContent, submitPhase, startPhaseTimer,
  } = usePracticeStore();

  const phase = phases[1];
  const topicPhase = phases[0];
  const suggestedMin = Math.round((phase?.suggested_seconds || 900) / 60);
  const [content, setContent] = useState(phase?.student_content || '');
  const [loading, setLoading] = useState(false);
  const [submitted, setSubmitted] = useState(!!phase?.submitted_at);

  // 启动正计时
  useEffect(() => {
    if (phase && !phase.submitted_at && !timerRunning && phaseElapsed === 0) {
      startPhaseTimer();
    }
  }, []);

  useEffect(() => {
    if (phase?.student_content !== undefined) {
      setContent(phase.student_content);
    }
  }, [phase?.student_content]);

  const handleSubmit = async () => {
    if (!content.trim()) {
      message.warning('请先写出你的构思提纲');
      return;
    }
    setLoading(true);
    try {
      const res = await practiceApi.savePhase({
        session_id: sessionId!,
        phase_type: 'outline',
        student_content: content.trim(),
        duration_seconds: phaseElapsed,
      });
      submitPhase(1, res.ai_feedback || '', res.references || []);
      setSubmitted(true);
      message.success('提纲已提交');
    } catch {
      // handled
    } finally {
      setLoading(false);
    }
  };

  const minutes = Math.floor(phaseElapsed / 60);
  const seconds = phaseElapsed % 60;
  const overSuggested = phase?.suggested_seconds > 0 && phaseElapsed > phase.suggested_seconds;

  return (
    <LoadingOverlay loading={loading} text="AI 正在对比分析你的提纲...">
      <Alert message={`题目：${topic}`} type="info" showIcon style={{ marginBottom: 16 }} />

      {/* 折叠展示阶段 1 学生分析 */}
      {topicPhase?.student_content && (
        <Collapse
          ghost
          style={{ marginBottom: 12 }}
          items={[{
            key: '1',
            label: '你的审题分析（点击展开）',
            children: (
              <div style={{ whiteSpace: 'pre-wrap', lineHeight: 1.8, color: '#555' }}>
                {topicPhase.student_content}
              </div>
            ),
          }]}
        />
      )}

      <Card
        title="阶段 2：构思提纲"
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
          根据你的审题分析，写出文章的构思提纲：引论、本论（分论点）、结论。建议用时 {suggestedMin} 分钟。
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
            setStudentContent(1, e.target.value);
          }}
          placeholder={"一、引论（开头）：...\n二、本论（主体）：\n  分论点1：...\n  分论点2：...\n  分论点3：...\n三、结论（结尾）：..."}
          rows={12}
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
            提交提纲
          </Button>
        )}
      </Card>

      {submitted && (
        <AnswerDisplay content={phase?.ai_feedback || null} title="AI 提纲对比" />
      )}
    </LoadingOverlay>
  );
};

export default OutlinePhase;
