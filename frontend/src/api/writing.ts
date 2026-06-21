import apiClient from './client';
import type {
  AnalyzeRequest, OutlineRequest, AssistRequest, EvaluateRequest,
  WritingResponse,
} from '../types/api';

// 播客素材相关类型
export interface MultiAiRequest {
  topic: string;
  models?: string[];
  grade_level?: string;
  topic_type?: string;
  thesis?: string;
  style?: string;
  essay?: string;
}

export interface MultiAiResult {
  ai_model: string;
  content: string;
  success: boolean;
  error?: string | null;
}

export interface ExportToPodcastRequest {
  stage: 'analysis' | 'outline' | 'essay' | 'evaluation';
  topic: string;
  content: string;
  ai_model: string;
  metadata?: Record<string, any>;
}

export interface PodcastMaterial {
  id: string;
  stage: string;
  topic: string;
  content: string;
  ai_model: string;
  status: string;
  created_at: string;
}

export interface GeneratePodcastRequest {
  material_ids: string[];
  prompt?: string;
  model?: string;
}

export interface GeneratePodcastTTSRequest {
  text: string;
  ref_audio: File;
  prompt_text: string;
  nfe?: number;
  guidance_strength?: number;
}

export interface GeneratePodcastTTSResponse {
  audio_url: string;
  duration_sec: number;
  message: string;
}

export const writingApi = {
  analyze: (params: AnalyzeRequest) =>
    apiClient.post<any, WritingResponse>('/writing/analyze', params),

  outline: (params: OutlineRequest) =>
    apiClient.post<any, WritingResponse>('/writing/outline', params),

  assist: (params: AssistRequest) =>
    apiClient.post<any, WritingResponse>('/writing/assist', params),

  evaluate: (params: EvaluateRequest) =>
    apiClient.post<any, WritingResponse>('/writing/evaluate', params),

  // 多AI并行生成接口
  multiAiAnalyze: (params: MultiAiRequest) =>
    apiClient.post<any, { success: boolean; results: MultiAiResult[]; count: number }>('/writing/multi-ai/analyze', params),

  multiAiOutline: (params: MultiAiRequest) =>
    apiClient.post<any, { success: boolean; results: MultiAiResult[]; count: number }>('/writing/multi-ai/outline', params),

  generateEssay: (params: { topic: string; outline: string; genre?: string; models?: string[] }) =>
    apiClient.post<any, { success: boolean; results: MultiAiResult[]; count: number }>('/writing/generate-essay', params),

  multiAiEvaluate: (params: MultiAiRequest) =>
    apiClient.post<any, { success: boolean; results: MultiAiResult[]; count: number }>('/writing/multi-ai/evaluate', params),

  // 播客素材导出接口
  exportToPodcast: (params: ExportToPodcastRequest) =>
    apiClient.post<any, { success: boolean; material_id: string; message: string }>('/writing/export-to-podcast', params),

  getPodcastMaterials: (params?: { topic?: string; stage?: string; status?: string }) =>
    apiClient.get<any, { success: boolean; materials: PodcastMaterial[]; count: number }>('/writing/podcast-materials', { params }),

  deletePodcastMaterial: (materialId: string) =>
    apiClient.delete<any, { success: boolean; message: string }>(`/writing/podcast-materials/${materialId}`),

  generatePodcastScript: (params: GeneratePodcastRequest) =>
    apiClient.post<any, { success: boolean; script: string; ai_model: string; materials_count: number }>('/writing/podcast-generate', params),

  // TTS语音生成接口（使用fetch避免axios问题）
  generatePodcastTTS: (params: GeneratePodcastTTSRequest) => {
    const formData = new FormData();
    formData.append('text', params.text);
    formData.append('ref_audio', params.ref_audio);
    formData.append('prompt_text', params.prompt_text);
    if (params.nfe !== undefined) formData.append('nfe', String(params.nfe));
    if (params.guidance_strength !== undefined) formData.append('guidance_strength', String(params.guidance_strength));
    
    console.log('[TTS API] 开始调用，文本长度:', params.text.length);
    const startTime = Date.now();
    
    // 使用原生fetch替代axios，避免multipart/form-data的问题
    return fetch('/writing/podcast-tts', {
      method: 'POST',
      body: formData,
      // 不要设置Content-Type，让浏览器自动设置boundary
    })
    .then(async response => {
      const elapsed = Date.now() - startTime;
      console.log('[TTS API] HTTP响应收到，耗时:', elapsed, 'ms, 状态码:', response.status);
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      console.log('[TTS API] JSON解析完成:', data);
      return data as GeneratePodcastTTSResponse;
    })
    .catch(error => {
      const elapsed = Date.now() - startTime;
      console.error('[TTS API] 请求失败，耗时:', elapsed, 'ms', error);
      throw error;
    });
  },
};
