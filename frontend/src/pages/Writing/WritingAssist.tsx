import React, { useState } from 'react';
import { Input, Button, Space, Row, Col, Typography, message, Alert, Card, Modal, Tabs } from 'antd';
import {
  EditOutlined,
  PlayCircleOutlined,
  HighlightOutlined,
  SwapOutlined,
  FileTextOutlined,
  SoundOutlined,
} from '@ant-design/icons';
import { useWritingStore } from '../../store/writingStore';
import { writingApi } from '../../api/writing';
import type { HelpType } from '../../types/api';
import AnswerDisplay from '../../components/writing/AnswerDisplay';
import LoadingOverlay from '../../components/common/LoadingOverlay';

const { Text, Paragraph } = Typography;
const { TabPane } = Tabs;

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
  const [generateModalVisible, setGenerateModalVisible] = useState(false);
  const [outline, setOutline] = useState('');
  const [generatedEssay, setGeneratedEssay] = useState<string | null>(null);
  const [generating, setGenerating] = useState(false);

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
              
              {/* 生成范文按钮 */}
              <Button
                icon={<FileTextOutlined />}
                onClick={() => setGenerateModalVisible(true)}
              >
                生成范文
              </Button>
            </Space>

            <AnswerDisplay content={assistResult} title="辅助建议" />
          </Card>
        </Col>
      </Row>

      {/* 生成范文弹窗 */}
      <Modal
        title="📝 基于提纲生成范文"
        open={generateModalVisible}
        onCancel={() => {
          setGenerateModalVisible(false);
          setGeneratedEssay(null);
        }}
        footer={null}
        width={800}
      >
        <Tabs defaultActiveKey="input">
          <TabPane tab="输入提纲" key="input">
            <Paragraph type="secondary">
              请输入你的构思提纲，AI将基于此生成一篇完整的范文供你参考。
            </Paragraph>
            
            <Input.TextArea
              value={outline}
              onChange={(e) => setOutline(e.target.value)}
              placeholder={`例如：\n一、引论：从现象入手，引出中心论点\n二、本论：\n  1. 分论点1 + 论据\n  2. 分论点2 + 论据\n  3. 分论点3 + 论据\n三、结论：总结全文，升华主题`}
              rows={12}
              style={{ marginBottom: 16, fontSize: 14, lineHeight: 1.8 }}
            />
            
            <Button
              type="primary"
              icon={<FileTextOutlined />}
              onClick={handleGenerateEssay}
              loading={generating}
              block
              size="large"
            >
              {generating ? '正在生成范文...' : '生成范文'}
            </Button>
          </TabPane>
          
          <TabPane tab="查看范文" key="output" disabled={!generatedEssay}>
            {generatedEssay && (
              <div>
                <div style={{ maxHeight: 600, overflowY: 'auto', overflowX: 'hidden', marginBottom: 16, padding: 12, border: '1px solid #f0f0f0', borderRadius: 4, backgroundColor: '#fafafa' }}>
                  <Paragraph style={{ whiteSpace: 'pre-wrap', lineHeight: 2, fontSize: 15, margin: 0 }}>
                    {generatedEssay}
                  </Paragraph>
                </div>
                
                <Space direction="vertical" style={{ width: '100%' }}>
                  <Button
                    icon={<SoundOutlined />}
                    onClick={handleExportToPodcast}
                    block
                  >
                    导出到播客模块
                  </Button>
                  <Text type="secondary" style={{ fontSize: 12 }}>
                    💡 提示：导出的范文可以在播客模块转换为语音，方便反复听读复习
                  </Text>
                </Space>
              </div>
            )}
          </TabPane>
        </Tabs>
      </Modal>
    </LoadingOverlay>
  );
};

export default WritingAssist;
