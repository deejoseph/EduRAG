import React, { useState } from 'react';
import { Steps, Card, Button, Space, Form, Input, Select, Typography, Tag, message } from 'antd';
import {
  ThunderboltOutlined,
  ClockCircleOutlined,
  RocketOutlined,
  ReloadOutlined,
} from '@ant-design/icons';
import { usePracticeStore } from '../../store/practiceStore';
import { practiceApi } from '../../api/practice';
import { TOPIC_TYPES, GRADE_LEVELS, DEFAULT_TOPIC_TYPE, DEFAULT_GRADE_LEVEL } from '../../constants';
import TopicPhase from './TopicPhase';
import OutlinePhase from './OutlinePhase';
import EssayPhase from './EssayPhase';
import EvalPhase from './EvalPhase';

const { Title, Text } = Typography;

const steps = [
  { title: '审题分析', description: '建议 10 分钟' },
  { title: '构思提纲', description: '建议 15 分钟' },
  { title: '正文写作', description: '建议 45 分钟' },
  { title: 'AI 评估', description: '综合评分' },
];

const stepComponents = [TopicPhase, OutlinePhase, EssayPhase, EvalPhase];

const formatElapsed = (seconds: number) => {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = seconds % 60;
  if (h > 0) return `${h}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
};

const PracticePage: React.FC = () => {
  const {
    sessionId, topic, status, currentPhase, phases, totalElapsed,
    initSession, setPhase, reset,
  } = usePracticeStore();

  const [form] = Form.useForm();
  const [starting, setStarting] = useState(false);

  const handleStart = async (values: { topic: string; topic_type: string; grade_level: string }) => {
    if (!values.topic.trim()) {
      message.warning('请输入作文题目');
      return;
    }
    setStarting(true);
    try {
      const res = await practiceApi.start({
        topic: values.topic.trim(),
        topic_type: values.topic_type,
        grade_level: values.grade_level,
      });
      initSession(
        res.session_id,
        res.session.topic,
        res.session.topic_type,
        res.session.grade_level,
        res.session.phases,
      );
      message.success('训练已开始，祝你好运！');
    } catch {
      // handled by interceptor
    } finally {
      setStarting(false);
    }
  };

  const handleReset = () => {
    reset();
    form.resetFields();
  };

  // === 未开始：显示开始表单 ===
  if (status === 'idle' || !sessionId) {
    return (
      <div className="page-container">
        <Card style={{ maxWidth: 640, margin: '40px auto' }}>
          <div style={{ textAlign: 'center', marginBottom: 24 }}>
            <ThunderboltOutlined style={{ fontSize: 48, color: '#1677ff' }} />
            <Title level={3} style={{ marginTop: 12 }}>强化训练</Title>
            <Text type="secondary">
              限时自主写作模式：先独立思考写作，再由 AI 评估反馈
            </Text>
          </div>

          <Form
            form={form}
            layout="vertical"
            onFinish={handleStart}
            initialValues={{
              topic_type: DEFAULT_TOPIC_TYPE,
              grade_level: DEFAULT_GRADE_LEVEL,
            }}
          >
            <Form.Item
              name="topic"
              label="作文题目"
              rules={[{ required: true, message: '请输入作文题目' }]}
            >
              <Input.TextArea
                rows={4}
                placeholder="粘贴或输入作文题目，例如：阅读下面的材料，根据要求写作..."
                style={{ fontSize: 15 }}
              />
            </Form.Item>

            <Form.Item name="topic_type" label="题型">
              <Select options={TOPIC_TYPES.map(t => ({ label: t.label, value: t.value }))} />
            </Form.Item>

            <Form.Item name="grade_level" label="学段">
              <Select options={GRADE_LEVELS.map(g => ({ label: g.label, value: g.value }))} />
            </Form.Item>

            <Form.Item>
              <Button
                type="primary"
                htmlType="submit"
                icon={<RocketOutlined />}
                size="large"
                block
                loading={starting}
              >
                开始训练
              </Button>
            </Form.Item>
          </Form>

          <div style={{ textAlign: 'center' }}>
            <Text type="secondary" style={{ fontSize: 12 }}>
              训练流程：审题(建议10min) → 提纲(建议15min) → 写作(建议45min) → AI评估
            </Text>
          </div>
        </Card>
      </div>
    );
  }

  // === 训练中 / 已完成 ===
  const CurrentComponent = stepComponents[currentPhase];

  return (
    <div className="page-container">
      {/* 全局信息栏 */}
      <Card size="small" style={{ marginBottom: 16 }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 8 }}>
          <div>
            <Text strong style={{ fontSize: 16 }}>{topic}</Text>
            <Tag color="blue" style={{ marginLeft: 8 }}>{status === 'completed' ? '已完成' : '训练中'}</Tag>
          </div>
          <Space>
            <Tag icon={<ClockCircleOutlined />} color="processing">
              总用时 {formatElapsed(totalElapsed)}
            </Tag>
          </Space>
        </div>
      </Card>

      {/* Steps */}
      <Card style={{ marginBottom: 16 }}>
        <Steps
          current={currentPhase}
          onChange={(idx) => {
            // 只允许切到已完成的阶段或下一阶段
            if (idx <= currentPhase || (phases[idx - 1]?.submitted_at)) {
              setPhase(idx);
            }
          }}
          items={steps}
          size="small"
        />
      </Card>

      {/* 阶段组件 */}
      <Card>
        <CurrentComponent />
      </Card>

      {/* 底部导航 */}
      <div style={{ marginTop: 16, display: 'flex', justifyContent: 'space-between' }}>
        <Button
          disabled={currentPhase === 0}
          onClick={() => setPhase(currentPhase - 1)}
        >
          上一步
        </Button>
        <Space>
          <Button icon={<ReloadOutlined />} danger onClick={handleReset}>
            结束训练
          </Button>
          <Button
            type="primary"
            disabled={currentPhase === steps.length - 1 || !phases[currentPhase]?.submitted_at}
            onClick={() => setPhase(currentPhase + 1)}
          >
            下一阶段
          </Button>
        </Space>
      </div>
    </div>
  );
};

export default PracticePage;
