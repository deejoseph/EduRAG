import React, { useState } from 'react';
import {
  Input, Button, Card, Row, Col, Select, Switch, Tag, Typography,
  Collapse, Space, Empty, Slider, InputNumber, message,
} from 'antd';
import {
  SearchOutlined, FilterOutlined, BulbOutlined,
  FileTextOutlined,
} from '@ant-design/icons';
import { searchApi } from '../../api/search';
import MarkdownRenderer from '../../components/common/MarkdownRenderer';
import LoadingOverlay from '../../components/common/LoadingOverlay';
import type { SearchResult, Filters } from '../../types/api';
import {
  DOC_CATEGORIES, QUESTION_TYPES, EXAM_REGIONS,
  GRADE_LEVELS, SUBJECTS, SOURCE_TYPES,
} from '../../constants';

const { Search: AntSearch } = Input;
const { Text, Paragraph } = Typography;

// 当前年份范围（动态生成近 10 年）
const currentYear = new Date().getFullYear();
const YEAR_OPTIONS = Array.from({ length: 10 }, (_, i) => {
  const y = currentYear - i;
  return { label: `${y}年`, value: y };
});

const FILE_TYPES = [
  { label: 'PDF', value: 'pdf' },
  { label: 'DOCX', value: 'docx' },
  { label: 'TXT', value: 'txt' },
  { label: 'MD', value: 'md' },
];

const Search: React.FC = () => {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<SearchResult[]>([]);
  const [llmAnswer, setLlmAnswer] = useState<string | null>(null);
  const [searched, setSearched] = useState(false);

  // 过滤条件
  const [showFilters, setShowFilters] = useState(false);
  const [filters, setFilters] = useState<Filters>({});
  const [withLlm, setWithLlm] = useState(false);
  const [topK, setTopK] = useState(10);
  const [scoreThreshold, setScoreThreshold] = useState(0.1); // 降低到0.1以获得更多结果

  const updateFilter = (key: keyof Filters, value: any) => {
    setFilters(prev => {
      if (value === undefined || value === null || value === '') {
        const next = { ...prev };
        delete next[key];
        return next;
      }
      return { ...prev, [key]: value };
    });
  };

  const handleSearch = async () => {
    if (!query.trim()) {
      message.warning('请输入搜索内容');
      return;
    }

    setLoading(true);
    setSearched(true);
    setResults([]);
    setLlmAnswer(null);

    try {
      const res = await searchApi.query({
        query: query.trim(),
        top_k: topK,
        score_threshold: scoreThreshold,
        with_llm: withLlm,
        filters: Object.keys(filters).length > 0 ? filters : undefined,
      });
      setResults(res.results || []);
      if (res.answer) setLlmAnswer(res.answer);
    } catch {
      // 错误已由拦截器处理
    } finally {
      setLoading(false);
    }
  };

  const renderMetaTags = (meta: Record<string, any>) => {
    const tags: React.ReactNode[] = [];
    if (meta.year) tags.push(<Tag color="blue" key="year">{meta.year}年</Tag>);
    if (meta.exam_region) tags.push(<Tag color="green" key="region">{meta.exam_region}</Tag>);
    if (meta.doc_category) tags.push(<Tag color="orange" key="cat">{meta.doc_category}</Tag>);
    if (meta.question_type) tags.push(<Tag color="purple" key="qt">{meta.question_type}</Tag>);
    if (meta.grade_level) tags.push(<Tag color="cyan" key="gl">{meta.grade_level}</Tag>);
    if (meta.subject) tags.push(<Tag key="sub">{meta.subject}</Tag>);
    if (meta.source_file) tags.push(<Tag color="default" key="file"><FileTextOutlined /> {meta.source_file}</Tag>);
    return tags;
  };

  const filterItems = [
    {
      key: 'filters',
      label: (
        <span>
          <FilterOutlined style={{ marginRight: 8 }} />
          高级筛选
          {Object.keys(filters).length > 0 && (
            <Tag color="blue" style={{ marginLeft: 8 }}>{Object.keys(filters).length} 项</Tag>
          )}
        </span>
      ),
      children: (
        <Row gutter={[16, 12]}>
          <Col xs={12} sm={8} md={6}>
            <Text type="secondary" style={{ fontSize: 12 }}>年份</Text>
            <Select
              allowClear placeholder="全部" style={{ width: '100%' }}
              options={YEAR_OPTIONS}
              value={filters.year}
              onChange={v => updateFilter('year', v)}
            />
          </Col>
          <Col xs={12} sm={8} md={6}>
            <Text type="secondary" style={{ fontSize: 12 }}>考区</Text>
            <Select
              allowClear placeholder="全部" style={{ width: '100%' }}
              options={EXAM_REGIONS as any}
              value={filters.exam_region}
              onChange={v => updateFilter('exam_region', v)}
            />
          </Col>
          <Col xs={12} sm={8} md={6}>
            <Text type="secondary" style={{ fontSize: 12 }}>文档类型</Text>
            <Select
              allowClear placeholder="全部" style={{ width: '100%' }}
              options={DOC_CATEGORIES as any}
              value={filters.doc_category}
              onChange={v => updateFilter('doc_category', v)}
            />
          </Col>
          <Col xs={12} sm={8} md={6}>
            <Text type="secondary" style={{ fontSize: 12 }}>题型</Text>
            <Select
              allowClear placeholder="全部" style={{ width: '100%' }}
              options={QUESTION_TYPES as any}
              value={filters.question_type}
              onChange={v => updateFilter('question_type', v)}
            />
          </Col>
          <Col xs={12} sm={8} md={6}>
            <Text type="secondary" style={{ fontSize: 12 }}>学段</Text>
            <Select
              allowClear placeholder="全部" style={{ width: '100%' }}
              options={GRADE_LEVELS as any}
              value={filters.grade_level}
              onChange={v => updateFilter('grade_level', v)}
            />
          </Col>
          <Col xs={12} sm={8} md={6}>
            <Text type="secondary" style={{ fontSize: 12 }}>科目</Text>
            <Select
              allowClear placeholder="全部" style={{ width: '100%' }}
              options={SUBJECTS as any}
              value={filters.subject}
              onChange={v => updateFilter('subject', v)}
            />
          </Col>
          <Col xs={12} sm={8} md={6}>
            <Text type="secondary" style={{ fontSize: 12 }}>来源类型</Text>
            <Select
              allowClear placeholder="全部" style={{ width: '100%' }}
              options={SOURCE_TYPES as any}
              value={filters.source_type}
              onChange={v => updateFilter('source_type', v)}
            />
          </Col>
          <Col xs={12} sm={8} md={6}>
            <Text type="secondary" style={{ fontSize: 12 }}>文件格式</Text>
            <Select
              allowClear placeholder="全部" style={{ width: '100%' }}
              options={FILE_TYPES}
              value={filters.file_type}
              onChange={v => updateFilter('file_type', v)}
            />
          </Col>
        </Row>
      ),
    },
  ];

  return (
    <div className="page-container">
      <h2 style={{ marginBottom: 24 }}>知识库检索</h2>

      {/* 搜索栏 */}
      <AntSearch
        size="large"
        placeholder="搜索范文、素材、真题、写作技巧..."
        enterButton={<><SearchOutlined /> 检索</>}
        value={query}
        onChange={e => setQuery(e.target.value)}
        onSearch={handleSearch}
        loading={loading}
        allowClear
      />

      {/* 搜索参数行 */}
      <Row gutter={16} style={{ marginTop: 12 }} align="middle">
        <Col>
          <Space>
            <Text type="secondary">返回数量:</Text>
            <InputNumber min={1} max={50} value={topK} onChange={v => setTopK(v || 10)} size="small" />
          </Space>
        </Col>
        <Col>
          <Space>
            <Text type="secondary">相似度阈值:</Text>
            <Slider
              min={0} max={1} step={0.05}
              value={scoreThreshold}
              onChange={setScoreThreshold}
              style={{ width: 120 }}
              tooltip={{ formatter: v => `${((v || 0) * 100).toFixed(0)}%` }}
            />
            <Text code>{(scoreThreshold * 100).toFixed(0)}%</Text>
          </Space>
        </Col>
        <Col>
          <Space>
            <BulbOutlined />
            <Text>LLM 增强回答</Text>
            <Switch checked={withLlm} onChange={setWithLlm} size="small" />
          </Space>
        </Col>
        <Col flex="auto" style={{ textAlign: 'right' }}>
          <Button
            type="link"
            onClick={() => setShowFilters(!showFilters)}
            icon={<FilterOutlined />}
          >
            {showFilters ? '收起筛选' : '展开筛选'}
          </Button>
        </Col>
      </Row>

      {/* 高级筛选 */}
      {showFilters && (
        <Collapse
          items={filterItems}
          defaultActiveKey={['filters']}
          ghost
          style={{ marginTop: 8, marginBottom: 16 }}
        />
      )}

      {/* 结果区域 */}
      <LoadingOverlay loading={loading} text="正在检索知识库...">
        {/* LLM 回答 */}
        {llmAnswer && (
          <Card
            title={<><BulbOutlined style={{ color: '#faad14' }} /> AI 综合分析</>}
            style={{ marginTop: 16, borderColor: '#faad14', borderWidth: 2 }}
          >
            <MarkdownRenderer content={llmAnswer} />
          </Card>
        )}

        {/* 检索结果列表 */}
        {searched && !loading && results.length === 0 && !llmAnswer && (
          <Empty
            description="未找到相关内容，请尝试其他关键词或调整筛选条件"
            style={{ marginTop: 48 }}
          />
        )}

        {results.length > 0 && (
          <>
            <Text type="secondary" style={{ display: 'block', marginTop: 16, marginBottom: 8 }}>
              共找到 {results.length} 条相关内容
            </Text>
            {results.map((item, idx) => (
              <Card
                key={idx}
                className="result-card"
                size="small"
                title={
                  <Space>
                    <Tag color={item.score >= 0.7 ? 'green' : item.score >= 0.4 ? 'blue' : 'default'}>
                      相似度 {(item.score * 100).toFixed(1)}%
                    </Tag>
                    <Text type="secondary">#{idx + 1}</Text>
                  </Space>
                }
              >
                <Paragraph ellipsis={{ rows: 4, expandable: true, symbol: '展开全文' }}>
                  {item.text}
                </Paragraph>
                <div style={{ marginTop: 8 }}>
                  {renderMetaTags(item.metadata)}
                </div>
              </Card>
            ))}
          </>
        )}
      </LoadingOverlay>
    </div>
  );
};

export default Search;
