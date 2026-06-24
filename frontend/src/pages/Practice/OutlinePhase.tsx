import React, { useState, useEffect } from 'react';
import { Input, Button, Alert, Card, Collapse, Tag, message, Space, Typography, Radio } from 'antd';
import { ClockCircleOutlined, SendOutlined, SoundOutlined } from '@ant-design/icons';
import MultiAiResults from '../../components/writing/MultiAiResults';
import { usePracticeStore } from '../../store/practiceStore';
import { practiceApi } from '../../api/practice';
import { writingApi } from '../../api/writing';
import AnswerDisplay from '../../components/writing/AnswerDisplay';
import LoadingOverlay from '../../components/common/LoadingOverlay';

const { Text } = Typography;

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
  
  // 多AI生成相关状态
  const [multiAiMode, setMultiAiMode] = useState(false); // 是否启用多AI模式
  const [multiAiResults, setMultiAiResults] = useState<any[]>([]);
  const [multiAiLoading, setMultiAiLoading] = useState(false);

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

  // 导出到播客模块
  const handleExportToPodcast = async () => {
    if (!phase?.ai_feedback) {
      message.warning('请先提交提纲，等待AI反馈后再导出');
      return;
    }
    
    try {
      const response = await writingApi.exportToPodcast({
        stage: 'outline',
        topic: topic || '未知题目',
        content: phase.ai_feedback,
        ai_model: 'qwen3:8b',
        metadata: {
          // 传递完整的练习上下文信息
          source: 'practice',  // 来源：强化训练
          practice_session_id: sessionId,  // 练习会话ID
          exported_at: new Date().toISOString(),
        },
      });
      message.success(`✅ 已导出到播客模块：${response.material_id}`);
    } catch (error) {
      console.error('导出失败:', error);
      message.error('导出失败');
    }
  };

  // 多AI并行生成播客素材
  const handleMultiAiGenerate = async () => {
    if (!topic.trim()) {
      message.warning('请先完成审题分析，获取题目内容');
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
      message.error('生成失败，请检查连接');
    } finally {
      setMultiAiLoading(false);
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
              <SendOutlined /> 普通模式
            </Radio.Button>
            <Radio.Button value={true}>
              <SoundOutlined /> 播客素材模式（多AI）
            </Radio.Button>
          </Radio.Group>
        </Space>
      </Card>

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
          <>
            {multiAiMode ? (
              <Button
                type="primary"
                icon={<SoundOutlined />}
                onClick={handleMultiAiGenerate}
                loading={multiAiLoading}
                style={{ marginTop: 12, background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }}
                block
                size="large"
              >
                一键生成播客素材（多AI并行）
              </Button>
            ) : (
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
          </>
        )}
      </Card>

      {submitted && (
        <div>
          <AnswerDisplay content={phase?.ai_feedback || null} title="AI 提纲对比" />
          
          {/* 导出到播客按钮 */}
          <Card size="small" style={{ marginTop: 16 }}>
            <Space direction="vertical" style={{ width: '100%' }}>
              <Text strong>🎙️ 播客素材生成</Text>
              <Text type="secondary" style={{ fontSize: 12 }}>
                将AI的提纲对比分析转换为播客文案，方便后续生成语音复习
              </Text>
              <Button
                icon={<SoundOutlined />}
                onClick={handleExportToPodcast}
                disabled={!phase?.ai_feedback}
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
            stage="outline"
            topic={topic}
            loading={multiAiLoading}
            onRegenerate={handleMultiAiGenerate}
          />
        </div>
      )}
    </LoadingOverlay>
  );
};

export default OutlinePhase;
