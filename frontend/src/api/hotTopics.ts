/**
 * 热点话题 API 封装
 */

import axios from 'axios';
import type {
  TopicCategory,
  HotTopicsResponse,
  PromptGeneratorRequest,
  PromptGeneratorResponse,
} from '../types/hotTopics';

const api = axios.create({
  baseURL: '/hot-topics',
  timeout: 180000, // LLM 调用可能需要较长时间，增加到3分钟
});

// 获取分类列表
export const getCategories = async (): Promise<{
  success: boolean;
  categories: TopicCategory[];
}> => {
  const response = await api.get('/categories');
  return response.data;
};

// 搜索热点话题
export const searchHotTopics = async (data: {
  category_id?: string;
  use_cache?: boolean;
  force_refresh?: boolean;
}): Promise<HotTopicsResponse> => {
  const response = await api.post('/search', data);
  return response.data;
};

// 刷新缓存
export const refreshCache = async (data: {
  category_id?: string;
}): Promise<{
  success: boolean;
  refreshed: number;
  errors: string[];
}> => {
  const response = await api.post('/refresh', data);
  return response.data;
};

// 自定义命题生成
export const generateCustomPrompt = async (
  data: PromptGeneratorRequest
): Promise<PromptGeneratorResponse> => {
  const response = await api.post('/prompt-generator', data);
  return response.data;
};
