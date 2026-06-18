import React, { useState, useEffect, useCallback } from 'react';
import { Input, Button, Alert, Card, Progress, Tag, message, Space, Typography } from 'antd';
import { ClockCircleOutlined, SendOutlined, SaveOutlined } from '@ant-design/icons';
import { usePracticeStore } from '../../store/practiceStore';
import { practiceApi } from '../../api/practice';
import LoadingOverlay from '../../components/common/LoadingOverlay';

const { Text } = Typography;

const EssayPhase: React.FC = () => {
  const {
    topic, sessionId, phases, phaseElapsed, timerRunning,
    setStudentContent, submitPhase, startPhaseTimer,
  } = usePracticeStore();

  const phase = phases[2];
  const suggestedMin = Math.round((phase?.suggested_seconds || 2700) / 60);
  const [essay, setEssay] = useState(phase?.student_content || '');
  const [loading, setLoading] = useState(false);
  const [submitted, setSubmitted] = useState(!!phase?.submitted_at);
  const [autoSaved, setAutoSaved] = useState(false);

  // 恢复 localStorage 草稿
  useEffect(() => {
    if (!submitted && sessionId) {
      const draft = localStorage.getItem(`practice_essay_${sessionId}`);
      if (draft && !essay) {
        setEssay(draft);
        setStudentContent(2, draft);
      }
    }
  }, []);

  // 启动正计时
  useEffect(() => {
    if (phase && !phase.submitted_at && !timerRunning && phaseElapsed === 0) {
      startPhaseTimer();
    }
  }, []);

  // 自动保存（每30秒）
  useEffect(() => {
    if (submitted || !sessionId) return;
    const interval = setInterval(() => {
      if (essay.trim()) {
        localStorage.setItem(`practice_essay_${sessionId}`, essay);
        setAutoSaved(true);
        setTimeout(() => setAutoSaved(false), 2000);
      }
    }, 30000);
    return () => clearInterval(interval);
  }, [essay, sessionId, submitted]);

  const handleSubmit = useCallback(async () => {
    if (!essay.trim()) {
      message.warning('请先写出你的作文');
      return;
    }
    setLoading(true);
    try {
      await practiceApi.savePhase({
        session_id: sessionId!,
        phase_type: 'essay',
        student_content: essay.trim(),
        duration_seconds: phaseElapsed,
      });
      submitPhase(2, '', []);
      setSubmitted(true);
      localStorage.removeItem(`practice_essay_${sessionId}`);
      message.success('作文已提交，进入评估阶段');
    } catch {
      // handled
    } finally {
      setLoading(false);
    }
  }, [essay, phaseElapsed, sessionId, submitPhase]);

  const minutes = Math.floor(phaseElapsed / 60);
  const seconds = phaseElapsed % 60;
  const charCount = essay.replace(/\s/g, '').length;
  const targetWords = 800;
  const progressPercent = Math.min(100, Math.round((charCount / targetWords) * 100));
  const overSuggested = phase?.suggested_seconds > 0 && phaseElapsed > phase.suggested_seconds;

  return (
    <LoadingOverlay loading={loading} text="正在保存作文...">
      <Alert message={`题目：${topic}`} type="info" showIcon style={{ marginBottom: 16 }} />

      <Card
        title="阶段 3：正文写作"
        extra={
          <Space>
            {!submitted && (
              <Tag icon={<ClockCircleOutlined />} color="processing" style={{ fontSize: 14, padding: '4px 12px' }}>
                已用 {String(minutes).padStart(2, '0')}:{String(seconds).padStart(2, '0')}
              </Tag>
            )}
            <Progress
              type="circle"
              percent={progressPercent}
              size={40}
              strokeColor={progressPercent >= 100 ? '#52c41a' : '#1890ff'}
              format={() => `${charCount}`}
            />
            <Text type="secondary">/ {targetWords} 字</Text>
            {autoSaved && <Text type="success" style={{ fontSize: 12 }}><SaveOutlined /> 已自动保存</Text>}
          </Space>
        }
        size="small"
      >
        <p style={{ color: '#666', marginBottom: 12 }}>
          根据你的提纲，完成全文写作。目标字数 800 字，建议用时 {suggestedMin} 分钟。
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
          value={essay}
          onChange={(e) => {
            setEssay(e.target.value);
            setStudentContent(2, e.target.value);
          }}
          placeholder="在此书写你的作文全文..."
          rows={20}
          disabled={submitted}
          className="essay-editor"
          style={{ fontSize: 16, lineHeight: 2, resize: 'vertical' }}
        />

        <div style={{ marginTop: 8, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Text type="secondary">
            已写 <Text strong>{charCount}</Text> 字
            {charCount >= targetWords && <Text type="success" style={{ marginLeft: 8 }}>已达目标字数</Text>}
          </Text>
          {!submitted && (
            <Button
              type="primary"
              icon={<SendOutlined />}
              onClick={handleSubmit}
              size="large"
            >
              提交作文
            </Button>
          )}
        </div>
      </Card>

      {submitted && (
        <Alert
          message="作文已提交"
          description="请进入下一阶段查看 AI 评估报告。"
          type="success"
          showIcon
          style={{ marginTop: 16 }}
        />
      )}
    </LoadingOverlay>
  );
};

export default EssayPhase;
