import apiClient from './client';
import type {
  SearchRequest, SearchResponse,
  HealthResponse, StatsResponse, CollectionsResponse,
  HotTopicsResponse,
} from '../types/api';

export const searchApi = {
  query: (params: SearchRequest) =>
    apiClient.post<any, SearchResponse>('/search/query', params),

  collections: () =>
    apiClient.get<any, CollectionsResponse>('/search/collections'),

  stats: () =>
    apiClient.get<any, StatsResponse>('/search/stats'),

  hotTopics: () =>
    apiClient.get<any, HotTopicsResponse>('/search/hot-topics'),
};

export const healthApi = {
  check: () =>
    apiClient.get<any, HealthResponse>('/health'),

  getModel: () =>
    apiClient.get<any, { success: boolean; model: string; available_models: Array<{value: string; label: string}> }>('/system/model'),

  setModel: (model: string) =>
    apiClient.post<any, { success: boolean; model: string; message: string }>('/system/model', { model }),
};
