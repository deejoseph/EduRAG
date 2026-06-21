/**
 * 多AI结果展示组件
 * 用于显示多个AI模型的生成结果，支持点选和导入播客模块
 */

import React, { useState } from 'react';
import { Card, Button, Space, Tag, message, Spin, Typography } from 'antd';
import { CheckCircleOutlined, ExportOutlined, ReloadOutlined, RobotOutlined } from '@ant-design/icons';
import type { MultiAiResult } from '../../api/writing';
import { writingApi } from '../../api/writing';

const { Text, Paragraph } = Typography;

interface MultiAiResultsProps {
  results: MultiAiResult[];
  stage: 'analysis' | 'outline' | 'essay' | 'evaluation';
  topic: string;
  loading?: boolean;
  onRegenerate?: () => void;
}

const MultiAiResults: React.FC<MultiAiResultsProps> = ({
  results,
  stage,
  topic,
  loading = false,
  onRegenerate,
}) => {
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [exporting, setExporting] = useState<Record<string, boolean>>({});

  // 处理导出到播客
  const handleExportToPodcast = async (result: MultiAiResult) => {
    if (!result.content || result.content.includes('生成回答时出错')) {
      message.warning('该结果内容为空或生成失败，无法导出');
      return;
    }

    setExporting((prev) => ({ ...prev, [result.ai_model]: true }));

    try {
      const response = await writingApi.exportToPodcast({
        stage,
        topic,
        content: result.content,
        ai_model: result.ai_model,
        metadata: {
          generated_at: new Date().toISOString(),
        },
      });

      if (response.success) {
        message.success(`✅ 已导入播客模块！素材ID: ${response.material_id}`);
        setSelectedId(result.ai_model);
      } else {
        message.error('导出失败');
      }
    } catch (error) {
      console.error('导出失败:', error);
      message.error('导出失败，请重试');
    } finally {
      setExporting((prev) => ({ ...prev, [result.ai_model]: false }));
    }
  };

  // 获取阶段标签颜色
  const getStageColor = (stage: string) => {
    const colors: Record<string, string> = {
      analysis: 'blue',
      outline: 'green',
      essay: 'purple',
      evaluation: 'orange',
    };
    return colors[stage] || 'default';
  };

  // 获取阶段中文名称
  const getStageName = (stage: string) => {
    const names: Record<string, string> = {
      analysis: '审题分析',
      outline: '构思提纲',
      essay: '范文生成',
      evaluation: '作文评估',
    };
    return names[stage] || stage;
  };

  if (loading) {
    return (
      <Card>
        <div style={{ textAlign: 'center', padding: '40px 0' }}>
          <Spin size="large" />
          <div style={{ marginTop: 16 }}>
            <Text type="secondary">正在调用多个AI模型生成内容，请稍候...</Text>
          </div>
        </div>
      </Card>
    );
  }

  if (!results || results.length === 0) {
    return (
      <Card>
        <div style={{ textAlign: 'center', padding: '40px 0' }}>
          <RobotOutlined style={{ fontSize: 48, color: '#d9d9d9' }} />
          <div style={{ marginTop: 16 }}>
            <Text type="secondary">暂无生成结果</Text>
          </div>
        </div>
      </Card>
    );
  }

  return (
    <Space direction="vertical" style={{ width: '100%' }} size="middle">
      {/* 标题栏 */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Space>
          <Tag color={getStageColor(stage)}>{getStageName(stage)}</Tag>
          <Text strong>多AI生成结果</Text>
          <Tag color="cyan">{results.length} 个模型</Tag>
        </Space>
        {onRegenerate && (
          <Button icon={<ReloadOutlined />} onClick={onRegenerate}>
            重新生成
          </Button>
        )}
      </div>

      {/* AI结果卡片 */}
      <Space direction="vertical" style={{ width: '100%' }} size="middle">
        {results.map((result, index) => {
          const isExported = selectedId === result.ai_model;
          const isGenerating = result.content.includes('生成回答时出错');

          return (
            <Card
              key={index}
              size="small"
              title={
                <Space>
                  <RobotOutlined />
                  <Text strong>{result.ai_model}</Text>
                  {isExported && (
                    <Tag icon={<CheckCircleOutlined />} color="success">
                      已导入
                    </Tag>
                  )}
                  {isGenerating && (
                    <Tag color="warning">生成超时</Tag>
                  )}
                </Space>
              }
              extra={
                <Button
                  type="primary"
                  size="small"
                  icon={<ExportOutlined />}
                  disabled={!result.content || isGenerating}
                  loading={exporting[result.ai_model]}
                  onClick={() => handleExportToPodcast(result)}
                >
                  导入播客模块
                </Button>
              }
              style={{
                borderLeft: isExported ? '4px solid #52c41a' : '4px solid transparent',
                transition: 'all 0.3s',
              }}
            >
              <Paragraph
                ellipsis={{ rows: 6, expandable: true, symbol: '展开' }}
                style={{ marginBottom: 0, whiteSpace: 'pre-wrap' }}
              >
                {result.content || '（无内容）'}
              </Paragraph>
            </Card>
          );
        })}
      </Space>

      {/* 提示说明 */}
      <Card size="small" style={{ background: '#f6ffed', border: '1px solid #b7eb8f' }}>
        <Space direction="vertical" style={{ width: '100%' }}>
          <Text type="secondary" style={{ fontSize: 12 }}>
            💡 <strong>使用提示：</strong>
          </Text>
          <ul style={{ margin: 0, paddingLeft: 20, fontSize: 12, color: '#666' }}>
            <li>每个AI模型会生成不同的结果，您可以对比选择最满意的内容</li>
            <li>点击【导入播客模块】按钮可将该内容保存到播客素材库</li>
            <li>不同阶段的素材可以混合搭配，形成完整的播客剧集</li>
            <li>如果生成超时，可以尝试重新生成或使用其他模型</li>
          </ul>
        </Space>
      </Card>
    </Space>
  );
};

export default MultiAiResults;
