import React, { useState, useEffect } from 'react';
import {
  Input, Button, Row, Col, Select, Switch, Tag, Typography,
  Collapse, Space, Empty, Slider, InputNumber, message, Alert, Card,
  Popconfirm,
} from 'antd';
import {
  SearchOutlined, FilterOutlined, BulbOutlined,
  FileTextOutlined, FireOutlined, StarFilled, StarOutlined,
  LinkOutlined,
} from '@ant-design/icons';
import { searchApi } from '../../api/search';
import { favoriteTopic, getFavorites } from '../../api/hotTopics';
import MarkdownRenderer from '../../components/common/MarkdownRenderer';
import LoadingOverlay from '../../components/common/LoadingOverlay';
import type { SearchResult, Filters, HotTopic } from '../../types/api';
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

  // 热门主题
  const [hotTopics, setHotTopics] = useState<HotTopic[]>([]);

  // 已收藏的题目（来自题库）
  const [favoritedTitles, setFavoritedTitles] = useState<Set<string>>(new Set());

  // 过滤条件
  const [showFilters, setShowFilters] = useState(false);
  const [filters, setFilters] = useState<Filters>({});
  const [withLlm, setWithLlm] = useState(false);
  const [topK, setTopK] = useState(10);
  const [scoreThreshold, setScoreThreshold] = useState(0.01); // 降低到0.01以支持更多查询

  // 加载热门主题
  useEffect(() => {
    loadHotTopics();
    loadFavorites();
  }, []);

  const loadFavorites = async () => {
    try {
      const res = await getFavorites();
      setFavoritedTitles(new Set(res.topics.map((t: any) => t.title)));
    } catch {
      // 静默失败
    }
  };

  // 收藏/取消收藏 RAG 热门主题
  const handleToggleFavorite = async (topic: HotTopic) => {
    const title = topic.name;
    const isFavorited = favoritedTitles.has(title);

    if (isFavorited) {
      try {
        const { unfavoriteTopic } = await import('../../api/hotTopics');
        await unfavoriteTopic(title);
        const next = new Set(favoritedTitles);
        next.delete(title);
        setFavoritedTitles(next);
        message.success('已取消收藏');
      } catch {
        message.error('取消收藏失败');
      }
    } else {
      const favoriteData = {
        title: topic.name,
        keywords: topic.keywords,
        category: '知识库热门',
        difficulty: '中等',
        relevance_score: Math.min(Math.round(topic.max_score * 10), 10),
        news_summary: topic.description,
        count: topic.count,
      };
      try {
        await favoriteTopic(favoriteData, 'rag');
        const next = new Set(favoritedTitles);
        next.add(title);
        setFavoritedTitles(next);
        message.success('已添加到题库 [RAG]');
      } catch (err: any) {
        const msg = err?.response?.data?.message || '收藏失败';
        message.warning(msg);
      }
    }
  };

  const loadHotTopics = async () => {
    try {
      const res = await searchApi.hotTopics();
      console.log('热门主题响应:', res);
      setHotTopics(res.topics || []);
    } catch (err) {
      console.error('加载热门主题失败:', err);
      // 即使失败也不影响页面显示
      setHotTopics([]);
    }
  };

  // 点击关键词搜索
  const handleKeywordClick = (keyword: string) => {
    setQuery(keyword);
    setTimeout(() => {
      // 触发搜索
      const searchEvent = new CustomEvent('trigger-search', { detail: keyword });
      window.dispatchEvent(searchEvent);
    }, 100);
  };

  // 尝试在新窗口打开文档
  const handleOpenDocument = (metadata: Record<string, any>) => {
    // 优先尝试 URL 字段（如果后端直接返回完整URL）
    const url = metadata.url || metadata.document_url || metadata.file_url;
    if (url) {
      window.open(url, '_blank');
      return;
    }

    // 尝试本地文件路径
    const filePath = metadata.source_file || metadata.file_path;
    if (filePath) {
      // 获取文件名
      const fileName = filePath.split(/[\\/]/).pop() || filePath;
      const ext = fileName.toLowerCase().split('.').pop();
      
      // 根据文件扩展名确定子目录
      let subDir = 'pdfs'; // 默认目录
      if (ext === 'docx' || ext === 'doc') {
        subDir = 'docs';
      } else if (ext === 'txt') {
        subDir = 'texts';
      } else if (ext === 'md') {
        subDir = 'markdowns';
      }
      
      // 构建 API URL
      const apiPath = `/search/files/${subDir}/${encodeURIComponent(fileName)}`;
      
      window.open(apiPath, '_blank');
      return;
    }

    message.warning('未找到可打开的文档链接');
  };

  // 检测匹配的热门主题
  const getMatchingTopics = () => {
    if (!query.trim() || !hotTopics.length) return [];
    
    const queryLower = query.toLowerCase();
    return hotTopics.filter(topic => 
      topic.name.toLowerCase().includes(queryLower) ||
      topic.keywords.some(kw => kw.toLowerCase().includes(queryLower))
    ).slice(0, 3);
  };

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

      {/* 热门主题区域 - 始终显示 */}
      {!loading && hotTopics.length > 0 && (
        <Card
          title={
            <>
              <FireOutlined style={{ color: '#ff4d4f' }} />
              高考作文热门主题{searched ? '（点击可快速检索）' : ''}
            </>
          }
          style={{ marginTop: searched ? 16 : 16 }}
          size={searched ? "small" : "default"}
        >
          <Row gutter={[12, 12]}>
            {hotTopics.slice(0, searched ? 4 : 8).map((topic) => {
              const isFavorited = favoritedTitles.has(topic.name);
              return (
              <Col xs={24} sm={12} md={8} lg={6} key={topic.name}>
                <div
                  onClick={() => handleKeywordClick(topic.keywords[0])}
                  className="topic-card"
                  style={{ cursor: 'pointer' }}
                >
                  <Card
                    size="small"
                    hoverable
                    extra={
                      <Popconfirm
                        title={isFavorited ? "确定取消收藏？" : "添加到题库？（RAG来源）"}
                        onConfirm={(e) => {
                          e?.stopPropagation();
                          handleToggleFavorite(topic);
                        }}
                        okText="确定"
                        cancelText="取消"
                      >
                        <Button
                          type={isFavorited ? 'primary' : 'default'}
                          size="small"
                          icon={isFavorited ? <StarFilled /> : <StarOutlined />}
                          onClick={(e) => e.stopPropagation()}
                        />
                      </Popconfirm>
                    }
                  >
                    <div style={{ marginBottom: 8 }}>
                      <Tag color="red">{topic.count}</Tag>
                      <Tag color="green">RAG</Tag>
                      <Text strong>{topic.name}</Text>
                    </div>
                    <div style={{ marginBottom: 8 }}>
                      {topic.keywords.map(kw => (
                        <Tag
                          key={kw}
                          style={{ cursor: 'pointer', marginBottom: 4 }}
                          onClick={(e) => {
                            e.stopPropagation();
                            handleKeywordClick(kw);
                          }}
                        >
                          {kw}
                        </Tag>
                      ))}
                    </div>
                    {!searched && (
                      <Text type="secondary" style={{ fontSize: 12 }}>
                        {topic.description}
                      </Text>
                    )}
                  </Card>
                </div>
              </Col>
              );
            })}
          </Row>
        </Card>
      )}

      {/* 结果区域 */}
      <LoadingOverlay loading={loading} text="正在检索知识库...">
        {/* 匹配主题提示 - 新增 */}
        {searched && !loading && results.length > 0 && (
          (() => {
            const matchingTopics = getMatchingTopics();
            return matchingTopics.length > 0 ? (
              <Alert
                message={
                  <>
                    <FireOutlined style={{ color: '#ff4d4f' }} />
                    {' '}相关热门主题
                  </>
                }
                description={
                  <div>
                    当前搜索与以下热门主题相关，这些可能是高考作文的重点方向：
                    <div style={{ marginTop: 8 }}>
                      {matchingTopics.map(topic => (
                        <Tag
                          key={topic.name}
                          color="red"
                          style={{ cursor: 'pointer', marginBottom: 4 }}
                          onClick={() => handleKeywordClick(topic.keywords[0])}
                        >
                          {topic.name} ({topic.count})
                        </Tag>
                      ))}
                    </div>
                  </div>
                }
                type="warning"
                showIcon
                style={{ marginBottom: 16 }}
              />
            ) : null;
          })()
        )}

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
            {results.map((item, idx) => {
              // 从 metadata 中提取文件路径
              const sourceFile = item.metadata.source_file || '';
              // 检查是否为支持的文档类型
              const supportedTypes = ['.pdf', '.docx', '.txt', '.md'];
              const hasDocument = supportedTypes.some(ext => 
                sourceFile.toLowerCase().endsWith(ext)
              );
              
              return (
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
                    {hasDocument && (
                      <Button
                        type="link"
                        size="small"
                        icon={<LinkOutlined />}
                        onClick={(e) => {
                          e.stopPropagation();
                          handleOpenDocument(item.metadata);
                        }}
                        style={{ padding: 0 }}
                      >
                        打开原文
                      </Button>
                    )}
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
              );
            })}
          </>
        )}
      </LoadingOverlay>
    </div>
  );
};

export default Search;
