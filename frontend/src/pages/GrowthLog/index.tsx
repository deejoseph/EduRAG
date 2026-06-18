import React, { useState, useEffect } from 'react';
import { Card, Row, Col, Typography, Button, Spin } from 'antd';
import {
  TrophyOutlined,
  RiseOutlined,
  ClockCircleOutlined,
  FireOutlined,
  ThunderboltOutlined,
} from '@ant-design/icons';
import {
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Area, AreaChart,
  BarChart, Bar, Legend,
  RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
} from 'recharts';
import { practiceApi } from '../../api/practice';
import type { GrowthLogResponse } from '../../types/practice';

const { Title, Text } = Typography;

const formatTime = (seconds: number) => {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  if (h > 0) return `${h}小时${m}分`;
  return `${m}分钟`;
};

const statCards = [
  {
    key: 'total_sessions',
    title: '总训练次数',
    icon: <FireOutlined style={{ fontSize: 24, color: '#fff' }} />,
    gradient: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    suffix: '次',
  },
  {
    key: 'average_score',
    title: '平均分',
    icon: <RiseOutlined style={{ fontSize: 24, color: '#fff' }} />,
    gradient: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
    suffix: '分',
  },
  {
    key: 'best_score',
    title: '最高分',
    icon: <TrophyOutlined style={{ fontSize: 24, color: '#fff' }} />,
    gradient: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
    suffix: '分',
  },
  {
    key: 'total_training_seconds',
    title: '累计训练时长',
    icon: <ClockCircleOutlined style={{ fontSize: 24, color: '#fff' }} />,
    gradient: 'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)',
    suffix: '',
    formatter: (val: number) => formatTime(val),
  },
];

const GrowthLogPage: React.FC = () => {
  const [data, setData] = useState<GrowthLogResponse | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchData = async () => {
    setLoading(true);
    try {
      const res = await practiceApi.growthLog();
      setData(res);
    } catch {
      // handled
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="page-container" style={{ textAlign: 'center', paddingTop: 100 }}>
        <Spin size="large" />
      </div>
    );
  }

  if (!data || data.sessions.length === 0) {
    return (
      <div className="page-container">
        <Card style={{ maxWidth: 600, margin: '60px auto', textAlign: 'center' }}>
          <ThunderboltOutlined style={{ fontSize: 64, color: '#d9d9d9', marginBottom: 16 }} />
          <Title level={4} style={{ color: '#666' }}>成长日志</Title>
          <Text type="secondary" style={{ display: 'block', marginBottom: 24, lineHeight: 2 }}>
            每一次训练都是成长的足迹。<br />
            完成你的第一次限时训练，这里将记录你的进步轨迹。
          </Text>
          <Button type="primary" size="large" href="/practice">
            开始第一次训练
          </Button>
        </Card>
      </div>
    );
  }

  const { summary, score_trend, phase_times, dimension_averages, sessions } = data;

  // 雷达图数据
  const radarData = [
    { dimension: '内容立意', value: dimension_averages.content, fullMark: 25 },
    { dimension: '结构安排', value: dimension_averages.structure, fullMark: 25 },
    { dimension: '语言表达', value: dimension_averages.language, fullMark: 25 },
    { dimension: '发展等级', value: dimension_averages.development, fullMark: 25 },
  ];

  // 最近一次维度分数
  const lastSession = sessions[sessions.length - 1];
  const hasLastScores = lastSession?.evaluation_scores;
  if (hasLastScores) {
    const es = lastSession.evaluation_scores!;
    radarData[0].value = es.content;
    radarData[1].value = es.structure;
    radarData[2].value = es.language;
    radarData[3].value = es.development;
  }

  return (
    <div className="page-container">
      {/* 页面标题 */}
      <div style={{ marginBottom: 24 }}>
        <Title level={3} style={{ margin: 0 }}>
          <RiseOutlined style={{ marginRight: 8, color: '#1677ff' }} />
          成长日志
        </Title>
        <Text type="secondary">记录你的每一次进步</Text>
      </div>

      {/* 统计卡片 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        {statCards.map((card) => {
          const val = (summary as any)[card.key] || 0;
          return (
            <Col xs={12} sm={12} md={6} key={card.key}>
              <Card
                style={{
                  background: card.gradient,
                  border: 'none',
                  borderRadius: 12,
                  overflow: 'hidden',
                }}
                styles={{ body: { padding: '20px 24px' } }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
                  <div style={{
                    width: 48, height: 48, borderRadius: 12,
                    background: 'rgba(255,255,255,0.25)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                  }}>
                    {card.icon}
                  </div>
                  <div>
                    <Text style={{ color: 'rgba(255,255,255,0.85)', fontSize: 13 }}>
                      {card.title}
                    </Text>
                    <div style={{ color: '#fff', fontSize: 28, fontWeight: 700, lineHeight: 1.2 }}>
                      {card.formatter ? card.formatter(val) : val}
                      {card.suffix && (
                        <span style={{ fontSize: 14, fontWeight: 400, marginLeft: 4 }}>
                          {card.suffix}
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              </Card>
            </Col>
          );
        })}
      </Row>

      {/* 分数趋势折线图 */}
      {score_trend.length > 0 && (
        <Card title="分数成长曲线" style={{ marginBottom: 24 }}>
          <ResponsiveContainer width="100%" height={280}>
            <AreaChart data={score_trend}>
              <defs>
                <linearGradient id="scoreGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#1677ff" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#1677ff" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="date" fontSize={12} tick={{ fill: '#999' }} />
              <YAxis domain={[0, 100]} fontSize={12} tick={{ fill: '#999' }} />
              <Tooltip
                contentStyle={{ borderRadius: 8, border: '1px solid #e8e8e8' }}
                formatter={(value: any) => [`${value} 分`, '得分']}
              />
              <Area
                type="monotone"
                dataKey="score"
                stroke="#1677ff"
                strokeWidth={2}
                fill="url(#scoreGradient)"
                dot={{ fill: '#1677ff', strokeWidth: 2, r: 4 }}
                activeDot={{ r: 6 }}
              />
            </AreaChart>
          </ResponsiveContainer>
        </Card>
      )}

      {/* 双栏：阶段用时 + 维度雷达 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} md={12}>
          <Card title="阶段用时趋势" style={{ height: '100%' }}>
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={phase_times}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="date" fontSize={12} tick={{ fill: '#999' }} />
                <YAxis fontSize={12} tick={{ fill: '#999' }}
                  tickFormatter={(v: number) => `${Math.round(v / 60)}m`}
                />
                <Tooltip
                  contentStyle={{ borderRadius: 8, border: '1px solid #e8e8e8' }}
                  formatter={(value: any, name: any) => {
                    const labels: Record<string, string> = {
                      topic: '审题分析', outline: '构思提纲', essay: '正文写作',
                    };
                    return [formatTime(Number(value)), labels[name] || name];
                  }}
                />
                <Legend
                  formatter={(value: string) => {
                    const labels: Record<string, string> = {
                      topic: '审题', outline: '提纲', essay: '写作',
                    };
                    return labels[value] || value;
                  }}
                />
                <Bar dataKey="topic" fill="#1677ff" radius={[4, 4, 0, 0]} />
                <Bar dataKey="outline" fill="#52c41a" radius={[4, 4, 0, 0]} />
                <Bar dataKey="essay" fill="#faad14" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </Card>
        </Col>

        <Col xs={24} md={12}>
          <Card title="评估维度分析" style={{ height: '100%' }}>
            <ResponsiveContainer width="100%" height={260}>
              <RadarChart data={radarData}>
                <PolarGrid stroke="#e8e8e8" />
                <PolarAngleAxis dataKey="dimension" fontSize={13} tick={{ fill: '#555' }} />
                <PolarRadiusAxis angle={90} domain={[0, 25]} fontSize={11} tick={{ fill: '#999' }} />
                <Tooltip
                  contentStyle={{ borderRadius: 8, border: '1px solid #e8e8e8' }}
                  formatter={(value: any) => [`${value}/25`, '得分']}
                />
                <Radar
                  name={hasLastScores ? '最近一次' : '历史平均'}
                  dataKey="value"
                  stroke="#1677ff"
                  fill="#1677ff"
                  fillOpacity={0.3}
                />
              </RadarChart>
            </ResponsiveContainer>
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default GrowthLogPage;
