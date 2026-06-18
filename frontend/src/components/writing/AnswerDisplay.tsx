import React from 'react';
import { Card } from 'antd';
import MarkdownRenderer from '../common/MarkdownRenderer';

interface AnswerDisplayProps {
  content: string | null;
  title?: string;
}

const AnswerDisplay: React.FC<AnswerDisplayProps> = ({ content, title = 'AI 分析结果' }) => {
  if (!content) return null;

  return (
    <Card title={title} style={{ marginTop: 16 }}>
      <MarkdownRenderer content={content} />
    </Card>
  );
};

export default AnswerDisplay;
