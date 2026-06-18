import apiClient from './client';
import type {
  AnalyzeRequest, OutlineRequest, AssistRequest, EvaluateRequest,
  WritingResponse,
} from '../types/api';

export const writingApi = {
  analyze: (params: AnalyzeRequest) =>
    apiClient.post<any, WritingResponse>('/writing/analyze', params),

  outline: (params: OutlineRequest) =>
    apiClient.post<any, WritingResponse>('/writing/outline', params),

  assist: (params: AssistRequest) =>
    apiClient.post<any, WritingResponse>('/writing/assist', params),

  evaluate: (params: EvaluateRequest) =>
    apiClient.post<any, WritingResponse>('/writing/evaluate', params),
};
