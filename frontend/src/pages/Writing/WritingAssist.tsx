import React, { useState } from 'react';
import { Input, Button, Space, Row, Col, Typography, message, Alert, Card } from 'antd';
import {
  EditOutlined,
  PlayCircleOutlined,
  HighlightOutlined,
  SwapOutlined,
} from '@ant-design/icons';
import { useWritingStore } from '../../store/writingStore';
import { writingApi } from '../../api/writing';
import type { HelpType } from '../../types/api';
import AnswerDisplay from '../../components/writing/AnswerDisplay';
import LoadingOverlay from '../../components/common/LoadingOverlay';

const { Text } = Typography;

const helpButtons = [
  { type: 'polish' as HelpType, label: '润色优化', icon: <EditOutlined /> },
  { type: 'continue' as HelpType, label: '续写建议', icon: <PlayCircleOutlined /> },
  { type: 'rhetoric' as HelpType, label: '修辞建议', icon: <HighlightOutlined /> },
  { type: 'transition' as HelpType, label: '过渡衔接', icon: <SwapOutlined /> },
];

const WritingAssist: React.FC = () => {
  const {
    topic, currentEssay, setCurrentEssay,
    assistResult, setAssistResult,
  } = useWritingStore();

  const [loading, setLoading] = useState(false);
  const [selectedHelp, setSelectedHelp] = useState<HelpType>('polish');

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

  const handleAssist = async (helpType: HelpType) => {
    if (!currentEssay.trim()) {
      message.warning('请先在左侧输入一些作文内容');
      return;
    }
    setSelectedHelp(helpType);
    setLoading(true);
    try {
      const res = await writingApi.assist({
        current_text: currentEssay.trim(),
        topic: topic.trim(),
        help_type: helpType,
      });
      setAssistResult(res.answer);
      message.success('辅助建议已生成');
    } catch (e) {
      // error handled by interceptor
    } finally {
      setLoading(false);
    }
  };

  const charCount = currentEssay.length;

  return (
    <LoadingOverlay loading={loading}>
      <Alert
        message={`当前题目：${topic}`}
        type="info"
        showIcon
        style={{ marginBottom: 16 }}
      />

      <Row gutter={16}>
        <Col xs={24} lg={12}>
          <Card title="作文编辑" extra={<Text type="secondary">{charCount} 字</Text>} size="small">
            <Input.TextArea
              value={currentEssay}
              onChange={(e) => setCurrentEssay(e.target.value)}
              placeholder="在此输入你的作文内容..."
              rows={18}
              className="essay-editor"
              style={{ resize: 'vertical' }}
            />
          </Card>
        </Col>

        <Col xs={24} lg={12}>
          <Card title="写作辅助" size="small">
            <Space wrap style={{ marginBottom: 16 }}>
              {helpButtons.map((btn) => (
                <Button
                  key={btn.type}
                  icon={btn.icon}
                  type={selectedHelp === btn.type ? 'primary' : 'default'}
                  onClick={() => handleAssist(btn.type)}
                  disabled={loading}
                >
                  {btn.label}
                </Button>
              ))}
            </Space>

            <AnswerDisplay content={assistResult} title="辅助建议" />
          </Card>
        </Col>
      </Row>
    </LoadingOverlay>
  );
};

export default WritingAssist;
