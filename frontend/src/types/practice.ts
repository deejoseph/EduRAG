// === 强化训练类型定义 ===

export type PhaseType = 'topic_analysis' | 'outline' | 'essay' | 'evaluation';

export interface PracticePhase {
  type: PhaseType;
  student_content: string;
  duration_seconds: number;
  suggested_seconds: number;
  ai_feedback: string | null;
  ai_references: Array<{ text: string; metadata: Record<string, any> }>;
  submitted_at: string | null;
}

export interface PracticeSession {
  id: string;
  topic: string;
  topic_type: string;
  grade_level: string;
  started_at: string;
  completed_at: string | null;
  total_time_seconds: number;
  status: 'in_progress' | 'completed' | 'abandoned';
  phases: PracticePhase[];
  total_score: number | null;
  include_in_log: boolean;
  evaluation_scores: EvaluationScores | null;
}

export interface EvaluationScores {
  content: number;
  structure: number;
  language: number;
  development: number;
}

// === API 请求 ===

export interface StartPracticeRequest {
  topic: string;
  topic_type?: string;
  grade_level?: string;
  essay_time_limit?: number; // 分钟（建议用时）
}

export interface StartPracticeResponse {
  success: boolean;
  session_id: string;
  session: PracticeSession;
}

export interface SavePhaseRequest {
  session_id: string;
  phase_type: PhaseType;
  student_content: string;
  duration_seconds: number;
}

export interface SavePhaseResponse {
  success: boolean;
  ai_feedback: string | null;
  references: Array<{ text: string; metadata: Record<string, any> }>;
  phase: PracticePhase;
}

export interface PracticeSessionSummary {
  id: string;
  topic: string;
  started_at: string;
  total_time_seconds: number;
  total_score: number | null;
  status: string;
  phase_count: number;
}

export interface PracticeHistoryResponse {
  success: boolean;
  sessions: PracticeSessionSummary[];
  total: number;
  page: number;
  page_size: number;
}

export interface SessionDetailResponse {
  success: boolean;
  session: PracticeSession;
}

// === 成长日志 ===

export interface GrowthLogSession {
  id: string;
  topic: string;
  started_at: string;
  total_score: number | null;
  total_time_seconds: number;
  phase_times: {
    topic_analysis: number;
    outline: number;
    essay: number;
  };
  evaluation_scores: EvaluationScores | null;
}

export interface GrowthLogSummary {
  total_sessions: number;
  average_score: number;
  best_score: number;
  total_training_seconds: number;
}

export interface GrowthLogResponse {
  success: boolean;
  sessions: GrowthLogSession[];
  summary: GrowthLogSummary;
  score_trend: Array<{ date: string; score: number }>;
  phase_times: Array<{ date: string; topic: number; outline: number; essay: number }>;
  dimension_averages: EvaluationScores;
}
