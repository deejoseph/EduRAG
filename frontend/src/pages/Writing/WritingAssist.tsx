import React, { useState } from 'react';
import { Input, Button, Space, Row, Col, Typography, message, Alert, Card, Radio } from 'antd';
import {
  EditOutlined,
  PlayCircleOutlined,
  HighlightOutlined,
  SwapOutlined,
  FileTextOutlined,
  SoundOutlined,
  StarOutlined,
} from '@ant-design/icons';
import { useWritingStore } from '../../store/writingStore';
import { writingApi } from '../../api/writing';
import type { HelpType } from '../../types/api';
import AnswerDisplay from '../../components/writing/AnswerDisplay';
import LoadingOverlay from '../../components/common/LoadingOverlay';
import MultiAiResults from '../../components/writing/MultiAiResults';

const { Text, Paragraph } = Typography;

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
  
  // 生成范文相关状态
  const [outline, setOutline] = useState('');
  const [generatedEssay, setGeneratedEssay] = useState<string | null>(null);
  const [generating, setGenerating] = useState(false);

  // 多AI生成相关状态
  const [multiAiMode, setMultiAiMode] = useState(false);
  const [multiAiResults, setMultiAiResults] = useState<any[]>([]);
  const [multiAiLoading, setMultiAiLoading] = useState(false);

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
      message.warning('请先输入一些作文内容');
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

  // 生成范文
  const handleGenerateEssay = async () => {
    if (!outline.trim()) {
      message.warning('请输入构思提纲');
      return;
    }
    
    setGenerating(true);
    try {
      const response = await writingApi.generateEssay({
        topic: topic || '未知题目',
        outline: outline.trim(),
        genre: '议论文',
      });
      
      // 提取第一个篇AI生成的范文
      if (response.results && response.results.length > 0) {
        const essayContent = response.results[0].content;
        setGeneratedEssay(essayContent);
        message.success('✅ 范文生成成功！');
      } else {
        message.error('范文生成失败，请重试');
      }
    } catch (error) {
      console.error('生成范文失败:', error);
      message.error('生成范文失败');
    } finally {
      setGenerating(false);
    }
  };

  // 导出范文到播客
  const handleExportToPodcast = async () => {
    if (!generatedEssay) {
      message.warning('请先生成范文');
      return;
    }
    
    try {
      const response = await writingApi.exportToPodcast({
        stage: 'essay',
        topic: topic || '未知题目',
        content: generatedEssay,
        ai_model: 'qwen3:8b',
      });
      message.success(`✅ 已导出到播客模块：${response.material_id}`);
    } catch (error) {
      console.error('导出失败:', error);
      message.error('导出失败');
    }
  };

  // 多AI并行生成播客素材
  const handleMultiAiGenerate = async () => {
    if (!currentEssay.trim()) {
      message.warning('请先在上方编辑区输入作文内容');
      return;
    }
    setMultiAiLoading(true);
    try {
      const res = await writingApi.multiAiAnalyze({
        topic: currentEssay.trim(),
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
      message.error('生成失败，请检查网络连接');
    } finally {
      setMultiAiLoading(false);
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

      {/* 模式切换 */}
      <Card size="small" style={{ marginBottom: 16, background: '#f0f5ff', border: '1px solid #adc6ff' }}>
        <Space>
          <StarOutlined style={{ color: '#1890ff' }} />
          <Text strong>生成模式：</Text>
          <Radio.Group
            value={multiAiMode}
            onChange={(e) => setMultiAiMode(e.target.value)}
            buttonStyle="solid"
          >
            <Radio.Button value={false}>普通模式</Radio.Button>
            <Radio.Button value={true}>
              <SoundOutlined /> 播客素材模式（多AI）
            </Radio.Button>
          </Radio.Group>
        </Space>
      </Card>

      {/* 作文编辑区 - 两种模式共用 */}
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col xs={24} lg={12}>
          <Card title="作文编辑" extra={<Text type="secondary">{charCount} 字</Text>} size="small">
            <Input.TextArea
              value={currentEssay}
              onChange={(e) => setCurrentEssay(e.target.value)}
              placeholder="在此输入你的作文内容..."
              rows={14}
              className="essay-editor"
              style={{ resize: 'vertical' }}
            />
          </Card>
        </Col>

        <Col xs={24} lg={12}>
          {/* 普通模式：写作辅助 */}
          {!multiAiMode && (
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
          )}

          {/* 播客模式：播客素材生成 */}
          {multiAiMode && (
            <Card title="🎙️ 播客素材生成" size="small">
              <Text type="secondary" style={{ display: 'block', marginBottom: 12 }}>
                将当前作文内容发送给多个AI，并行生成播客素材文案
              </Text>
              <Button
                type="primary"
                icon={<SoundOutlined />}
                onClick={handleMultiAiGenerate}
                size="large"
                block
                loading={multiAiLoading}
                style={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }}
              >
                一键生成播客素材（多AI并行）
              </Button>
            </Card>
          )}
        </Col>
      </Row>

      {/* 多AI结果展示 */}
      {multiAiMode && multiAiResults.length > 0 && (
        <MultiAiResults
          results={multiAiResults}
          stage="essay"
          topic={topic}
          loading={multiAiLoading}
          onRegenerate={handleMultiAiGenerate}
        />
      )}

      {/* 生成范文区域 - 两种模式共用 */}
      <Card 
        title="📝 基于提纲生成范文" 
        size="small" 
        style={{ marginTop: 16 }}
      >
        <Row gutter={16}>
          <Col xs={24} md={12}>
            <Text strong style={{ display: 'block', marginBottom: 8 }}>输入提纲：</Text>
            <Input.TextArea
              value={outline}
              onChange={(e) => setOutline(e.target.value)}
              placeholder={`例如：\n一、引论：从现象入手，引出中心论点\n二、本论：\n  分论点1 + 论据\n  分论点2 + 论据\n  分论点3 + 论据\n三、结论：总结全文，升华主题`}
              rows={10}
              style={{ fontSize: 14, lineHeight: 1.8 }}
            />
            <Button
              type="primary"
              icon={<FileTextOutlined />}
              onClick={handleGenerateEssay}
              loading={generating}
              block
              size="large"
              style={{ marginTop: 12 }}
            >
              {generating ? '正在生成范文...' : '生成范文'}
            </Button>
          </Col>

          <Col xs={24} md={12}>
            <Text strong style={{ display: 'block', marginBottom: 8 }}>生成的范文：</Text>
            {generatedEssay ? (
              <div>
                <div style={{ maxHeight: 400, overflowY: 'auto', overflowX: 'hidden', padding: 12, border: '1px solid #f0f0f0', borderRadius: 4, backgroundColor: '#fafafa' }}>
                  <Paragraph style={{ whiteSpace: 'pre-wrap', lineHeight: 2, fontSize: 15, margin: 0 }}>
                    {generatedEssay}
                  </Paragraph>
                </div>
                <Button
                  icon={<SoundOutlined />}
                  onClick={handleExportToPodcast}
                  block
                  style={{ marginTop: 12 }}
                >
                  导出到播客模块
                </Button>
                <Text type="secondary" style={{ fontSize: 12, display: 'block', marginTop: 8 }}>
                  💡 导出的范文可以在播客模块转换为语音，方便反复听读复习
                </Text>
              </div>
            ) : (
              <div style={{ padding: 40, textAlign: 'center', color: '#999', border: '1px dashed #d9d9d9', borderRadius: 4 }}>
                <FileTextOutlined style={{ fontSize: 32, marginBottom: 8 }} />
                <div>输入提纲后点击"生成范文"</div>
              </div>
            )}
          </Col>
        </Row>
      </Card>
    </LoadingOverlay>
  );
};

export default WritingAssist;
