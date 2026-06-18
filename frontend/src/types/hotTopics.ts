/**
 * 热点话题相关类型定义
 */

export interface TopicCategory {
  id: string;
  name: string;
  keywords: string[];
  search_queries: string[];
}

export interface HotTopic {
  title: string;
  category: string;
  keywords: string[];
  news_summary: string;
  essay_prompt: string;
  writing_angles: string[];
  reference_materials: string[];
  difficulty: '容易' | '中等' | '较难';
  relevance_score: number;
}

export interface HotTopicsResponse {
  success: boolean;
  topics: HotTopic[];
  total: number;
  generated_at: string;
}

export interface PromptGeneratorRequest {
  keywords: string[];
  essay_type?: string;
  difficulty?: string;
}

export interface PromptGeneratorResponse {
  success: boolean;
  prompt: string;
  keywords: string[];
  essay_type: string;
  difficulty: string;
}
