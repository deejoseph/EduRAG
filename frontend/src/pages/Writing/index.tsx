import React from 'react';
import { Steps, Card, Button, Space } from 'antd';
import { useWritingStore } from '../../store/writingStore';
import TopicAnalysis from './TopicAnalysis';
import OutlineGen from './OutlineGen';
import WritingAssist from './WritingAssist';
import EssayEval from './EssayEval';

const steps = [
  { title: '审题分析', description: '理解题目要求' },
  { title: '构思提纲', description: '规划文章结构' },
  { title: '写作辅助', description: '润色与优化' },
  { title: '作文评估', description: '多维评分反馈' },
];

const stepComponents = [TopicAnalysis, OutlineGen, WritingAssist, EssayEval];

const WritingPage: React.FC = () => {
  const { currentStep, setStep, reset } = useWritingStore();
  const CurrentComponent = stepComponents[currentStep];

  return (
    <div className="page-container">
      <Card style={{ marginBottom: 24 }}>
        <Steps
          current={currentStep}
          onChange={setStep}
          items={steps}
          size="small"
        />
      </Card>

      <Card>
        <CurrentComponent />
      </Card>

      <div style={{ marginTop: 16, display: 'flex', justifyContent: 'space-between' }}>
        <Button
          disabled={currentStep === 0}
          onClick={() => setStep(currentStep - 1)}
        >
          上一步
        </Button>
        <Space>
          <Button danger onClick={reset}>重置</Button>
          <Button
            type="primary"
            disabled={currentStep === steps.length - 1}
            onClick={() => setStep(currentStep + 1)}
          >
            下一步
          </Button>
        </Space>
      </div>
    </div>
  );
};

export default WritingPage;
