import apiClient from './client';
import type {
  StartPracticeRequest, StartPracticeResponse,
  SavePhaseRequest, SavePhaseResponse,
  PracticeHistoryResponse, SessionDetailResponse,
  GrowthLogResponse,
} from '../types/practice';

export const practiceApi = {
  start: (params: StartPracticeRequest) =>
    apiClient.post<any, StartPracticeResponse>('/practice/start', params),

  savePhase: (params: SavePhaseRequest) =>
    apiClient.post<any, SavePhaseResponse>('/practice/save-phase', params),

  history: (page = 1, pageSize = 20) =>
    apiClient.get<any, PracticeHistoryResponse>('/practice/history', {
      params: { page, page_size: pageSize },
    }),

  getSession: (sessionId: string) =>
    apiClient.get<any, SessionDetailResponse>(`/practice/${sessionId}`),

  deleteSession: (sessionId: string) =>
    apiClient.delete<any, { success: boolean; message: string }>(`/practice/${sessionId}`),

  toggleLog: (sessionId: string, include: boolean) =>
    apiClient.patch<any, { success: boolean; include_in_log: boolean }>(
      `/practice/${sessionId}/toggle-log`, { include_in_log: include },
    ),

  saveRecord: (sessionId: string, save: boolean) =>
    apiClient.patch<any, { success: boolean; save_to_record: boolean }>(
      `/practice/${sessionId}/save-record`, { save_to_record: save },
    ),

  growthLog: () =>
    apiClient.get<any, GrowthLogResponse>('/practice/growth-log'),

  resetLog: () =>
    apiClient.delete<any, { success: boolean; deleted: number }>('/practice/reset-log'),
};
