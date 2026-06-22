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
  in_rag?: boolean; // 是否已存入RAG知识库
  rag_added_at?: string; // 存入RAG的时间
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

// 播客文案类型定义
export interface PodcastScript {
  script_id: string;
  title: string;
  topic: string;
  version: number;
  parent_id?: string | null;
  status: 'draft' | 'completed' | 'archived';
  stage?: 'shenti' | 'gousi' | 'xiezuo' | 'pinggu'; // 写作阶段
  created_at: string;
  updated_at: string;
  materials_count: number;
  model: string;
  content?: string; // 获取单个文案时包含内容
  // 作文相关字段(从metadata中提取)
  question_type?: string; // 题目类型
  question_name?: string; // 题库题目名称
}

export interface PodcastScriptsListResponse {
  success: boolean;
  scripts: PodcastScript[];
  count: number;
}

export interface PodcastScriptDetailResponse {
  success: boolean;
  script: PodcastScript;
}

export interface DuplicateScriptResponse {
  success: boolean;
  new_script_id: string;
  version: number;
  title: string;
}

// 参考音频类型定义
export interface RefAudio {
  id: string;
  name: string;
  path: string;
  size: number;
  created_at: number;
  prompt_text?: string;  // 参考音频对应的文本
}

export interface RefAudiosListResponse {
  success: boolean;
  audios: RefAudio[];
}

export interface UploadRefAudioResponse {
  success: boolean;
  id: string;
  name: string;
  path: string;
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

  // 将播客素材存入RAG知识库
  addPodcastMaterialToRag: (materialId: string, data?: { content?: string; title?: string }) =>
    apiClient.post<any, { success: boolean; message: string; chunk_count: number; collection: string }>(
      `/writing/podcast-materials/${materialId}/add-to-rag`,
      data || {}
    ),

  // 生成播客文案的RSS Feed
  generatePodcastRSS: (params?: { script_ids?: string[]; topic?: string; limit?: number }) => {
    const queryParams: Record<string, any> = {};
    if (params?.script_ids) queryParams.script_ids = params.script_ids.join(',');
    if (params?.topic) queryParams.topic = params.topic;
    if (params?.limit) queryParams.limit = params.limit;
    
    return apiClient.get<any, { success: boolean; rss_xml: string; download_url: string; count: number }>(
      '/writing/podcast-scripts/rss',
      { params: queryParams }
    );
  },

  // 更新播客文案状态
  updatePodcastScriptStatus: (scriptId: string, status: 'draft' | 'completed' | 'archived') =>
    apiClient.put<any, { success: boolean; message: string; new_status: string; script_id: string }>(
      `/writing/podcast-scripts/${scriptId}/status`,
      { status }
    ),

  // 更新播客文案阶段
  updatePodcastScriptStage: (scriptId: string, stage: 'shenti' | 'gousi' | 'xiezuo' | 'pinggu') =>
    apiClient.put<any, { success: boolean; message: string; new_stage: string; script_id: string }>(
      `/writing/podcast-scripts/${scriptId}/stage`,
      { stage }
    ),

  // 音频关联管理接口
  addAudioAssociation: (scriptId: string, audioId: string) =>
    apiClient.post<any, { success: boolean; message: string; script_id: string; audio_id: string }>(
      `/writing/podcast-scripts/${scriptId}/audio-association`,
      { audio_id: audioId }
    ),

  removeAudioAssociation: (scriptId: string, audioId: string) =>
    apiClient.delete<any, { success: boolean; message: string; script_id: string; audio_id: string }>(
      `/writing/podcast-scripts/${scriptId}/audio-association`,
      { data: { audio_id: audioId } }
    ),

  getScriptAudioFiles: (scriptId: string) =>
    apiClient.get<any, { success: boolean; audio_files: Array<{ audio_id: string; filename: string; duration?: number; file_size?: number; created_at?: string }> }>(
      `/writing/podcast-scripts/${scriptId}/audio-files`
    ),

  generatePodcastScript: (params: GeneratePodcastRequest) =>
    apiClient.post<any, { success: boolean; script: string; ai_model: string; materials_count: number; script_metadata?: any }>('/writing/podcast-generate', params),

  // 播客文案管理接口
  getPodcastScripts: (params?: { topic?: string; status?: string; limit?: number }) =>
    apiClient.get<any, PodcastScriptsListResponse>('/writing/podcast-scripts', { params }),

  getPodcastScript: (scriptId: string) =>
    apiClient.get<any, PodcastScriptDetailResponse>(`/writing/podcast-scripts/${scriptId}`),

  deletePodcastScript: (scriptId: string) =>
    apiClient.delete<any, { success: boolean; message: string }>(`/writing/podcast-scripts/${scriptId}`),

  duplicatePodcastScript: (scriptId: string) =>
    apiClient.post<any, DuplicateScriptResponse>(`/writing/podcast-scripts/${scriptId}/duplicate`),

  // TTS语音生成接口（使用fetch避免axios问题）
  generatePodcastTTS: (params: GeneratePodcastTTSRequest | { text: string; ref_audio_id: string; prompt_text: string; nfe?: number; guidance_strength?: number }) => {
    const formData = new FormData();
    formData.append('text', params.text);
    
    // 支持两种模式：上传文件或引用已保存的音频ID
    if ('ref_audio' in params) {
      formData.append('ref_audio', params.ref_audio);
    } else if ('ref_audio_id' in params) {
      formData.append('ref_audio_id', params.ref_audio_id);
    }
    
    formData.append('prompt_text', params.prompt_text);
    if (params.nfe !== undefined) formData.append('nfe', String(params.nfe));
    if (params.guidance_strength !== undefined) formData.append('guidance_strength', String(params.guidance_strength));
    
    const ttsUrl = '/writing/podcast-tts';
    console.log('[TTS API] 请求URL:', ttsUrl);
    console.log('[TTS API] 当前页面URL:', window.location.href);
    console.log('[TTS API] 开始调用，文本长度:', params.text.length);
    const startTime = Date.now();
    
    // 使用原生fetch替代axios，避免multipart/form-data的问题
    return fetch(ttsUrl, {
      method: 'POST',
      body: formData,
      // 不要设置Content-Type，让浏览器自动设置boundary
    })
    .then(async response => {
      const elapsed = Date.now() - startTime;
      console.log('[TTS API] HTTP响应收到，耗时:', elapsed, 'ms, 状态码:', response.status, 'URL:', response.url);
      
      if (!response.ok) {
        const bodyText = await response.text();
        console.error('[TTS API] 错误响应体:', bodyText);
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
  
  // 参考音频管理接口
  getRefAudios: () =>
    apiClient.get<any, RefAudiosListResponse>('/writing/podcast-ref-audios'),
  
  uploadRefAudio: (file: File, promptText?: string) => {
    const formData = new FormData();
    formData.append('ref_audio', file);
    if (promptText) {
      formData.append('prompt_text', promptText);
    }
    
    return fetch('/writing/podcast-ref-audios/upload', {
      method: 'POST',
      body: formData,
    })
    .then(async response => {
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      const data = await response.json();
      return data as UploadRefAudioResponse;
    });
  },
  
  // 更新参考音频的文本
  updateRefAudioText: (audioId: string, promptText: string) =>
    apiClient.put<any, { success: boolean; message: string }>(`/writing/podcast-ref-audios/${audioId}/text`, { prompt_text: promptText }),
  
  deleteRefAudio: (filename: string) =>
    apiClient.delete<any, { success: boolean; message: string }>(`/writing/podcast-ref-audios/${filename}`),
};
