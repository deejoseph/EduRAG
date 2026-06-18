import apiClient from './client';
import type {
  SearchRequest, SearchResponse,
  HealthResponse, StatsResponse, CollectionsResponse,
} from '../types/api';

export const searchApi = {
  query: (params: SearchRequest) =>
    apiClient.post<any, SearchResponse>('/search/query', params),

  collections: () =>
    apiClient.get<any, CollectionsResponse>('/search/collections'),

  stats: () =>
    apiClient.get<any, StatsResponse>('/search/stats'),
};

export const healthApi = {
  check: () =>
    apiClient.get<any, HealthResponse>('/health'),
};
