// === 通用类型 ===

export interface Reference {
  text: string;
  metadata: Record<string, any>;
}

export interface WritingResponse {
  success: boolean;
  answer: string;
  references: Reference[];
  ref_count: number;
}

export interface Filters {
  year?: number;
  exam_region?: string;
  doc_category?: string;
  file_type?: string;
  question_type?: string;
  grade_level?: string;
  subject?: string;
  source_type?: string;
}

// === 写作训练请求 ===

export interface AnalyzeRequest {
  topic: string;
  topic_type?: string;
  grade_level?: string;
  top_k?: number;
  score_threshold?: number;
  filters?: Filters;
  rerank?: boolean | null;
}

export interface OutlineRequest {
  topic: string;
  thesis?: string;
  style?: string;
  word_count?: number;
  top_k?: number;
  score_threshold?: number;
  filters?: Filters;
  rerank?: boolean | null;
}

export type HelpType = 'polish' | 'continue' | 'rhetoric' | 'transition';

export interface AssistRequest {
  current_text: string;
  topic: string;
  help_type?: HelpType;
  context?: string;
  top_k?: number;
  score_threshold?: number;
  filters?: Filters;
  rerank?: boolean | null;
}

export interface EvaluateRequest {
  essay: string;
  topic?: string;
  grade_level?: string;
  scoring_rubric?: string[];
  top_k?: number;
  score_threshold?: number;
  filters?: Filters;
  rerank?: boolean | null;
}

// === 搜索 ===

export interface SearchRequest {
  query: string;
  collection?: string;
  top_k?: number;
  score_threshold?: number;
  with_llm?: boolean;
  role?: string;
  expertise?: string;
  filters?: Filters;
  rerank?: boolean | null;
}

export interface SearchResult {
  text: string;
  score: number;
  metadata: Record<string, any>;
}

export interface SearchResponse {
  success: boolean;
  results: SearchResult[];
  count: number;
  answer?: string;
}

// === 系统 ===

export interface HealthResponse {
  status: string;
  model: string;
  embedding_model: string;
  timestamp: string;
}

export interface CollectionInfo {
  name: string;
  count: number;
  metadata?: Record<string, any>;
}

export interface StatsResponse {
  success: boolean;
  total_collections: number;
  total_documents: number;
  collections: CollectionInfo[];
  llm_model: string;
  embedding_model: string;
}

export interface CollectionsResponse {
  success: boolean;
  collections: CollectionInfo[];
}
