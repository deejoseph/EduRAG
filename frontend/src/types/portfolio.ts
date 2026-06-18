/**
 * 作品集相关类型定义
 */

export interface PortfolioItem {
  id: string;
  title: string;
  content: string;
  topic: string;
  source: 'writing' | 'practice' | 'upload' | 'manual';

  // 高考作文元数据
  essay_type?: string;        // 作文类型：材料作文/话题作文/命题作文/半命题作文
  essay_style?: string;       // 文体：议论文/记叙文/说明文/散文
  grade_level?: string;       // 学段：高中/初中
  exam_year?: number;         // 高考年份（如来自真题）
  exam_region?: string;       // 考区：全国卷/北京卷/上海卷等
  keywords?: string[];        // 关键词/主题词
  word_count?: number;        // 作文字数

  // 评分信息
  score?: number;
  evaluation_scores?: {
    content?: number;         // 内容立意 /25
    structure?: number;       // 结构安排 /25
    language?: number;        // 语言表达 /25
    development?: number;     // 发展等级 /25
  };

  // AI 反馈
  ai_feedback?: string;
  references?: Array<{
    text: string;
    metadata: Record<string, any>;
  }>;

  // 标签和笔记
  tags: string[];
  notes: string;

  // 时间戳
  created_at: string;
  updated_at: string;

  // 其他
  starred: boolean;
  metadata: Record<string, any>;
}

export interface PortfolioItemSummary {
  id: string;
  title: string;
  topic: string;
  source: string;

  // 高考作文元数据
  essay_type?: string;
  essay_style?: string;
  grade_level?: string;
  exam_year?: number;
  exam_region?: string;
  keywords?: string[];
  word_count?: number;

  // 评分
  score?: number;
  starred: boolean;

  // 时间
  created_at: string;
  updated_at: string;

  // 预览
  content_preview: string;
  has_ai_feedback: boolean;
  has_notes: boolean;
  tags: string[];
}

export interface PortfolioListResponse {
  success: boolean;
  items: PortfolioItemSummary[];
  total: number;
  page: number;
  page_size: number;
}

export interface PortfolioStats {
  total_items: number;
  tagged_items: number;
  starred_items: number;
  scored_items: number;
  average_score: number;
  best_score: number;
  sources: Record<string, number>;
  top_tags: Array<{ name: string; count: number }>;
  essay_types: Record<string, number>;
  essay_styles: Record<string, number>;
}

export interface TagInfo {
  name: string;
  count: number;
}

// 排序配置
export type SortField = 'created_at' | 'updated_at' | 'score' | 'title' | 'exam_year' | 'word_count';
export type SortOrder = 'asc' | 'desc';

export interface SortConfig {
  field: SortField;
  order: SortOrder;
}

// 筛选配置
export interface FilterConfig {
  keyword?: string;
  tag?: string;
  source?: string;
  essay_type?: string;
  essay_style?: string;
  grade_level?: string;
  exam_year?: number;
  exam_region?: string;
  starred?: boolean;
  min_score?: number;
  max_score?: number;
}
