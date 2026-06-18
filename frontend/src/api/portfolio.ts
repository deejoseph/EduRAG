/**
 * 作品集 API 封装
 */

import axios from 'axios';
import type {
  PortfolioItem,
  PortfolioListResponse,
  PortfolioStats,
  TagInfo,
} from '../types/portfolio';

const api = axios.create({
  baseURL: '/portfolio',
  timeout: 30000,
});

// 添加作品到作品集
export const addToPortfolio = async (data: {
  content: string;
  title?: string;
  topic?: string;
  source?: string;
  metadata?: Record<string, any>;
  tags?: string[];
  ai_feedback?: string;
  references?: Array<{ text: string; metadata: Record<string, any> }>;
  score?: number;
  evaluation_scores?: any;
  notes?: string;
}): Promise<{ success: boolean; item_id: string; item: PortfolioItem }> => {
  const response = await api.post('/add', data);
  return response.data;
};

// 获取作品集列表
export const getPortfolioList = async (params: {
  page?: number;
  page_size?: number;
  tag?: string;
  source?: string;
  keyword?: string;
  starred?: boolean;
  sort_by?: 'created_at' | 'updated_at' | 'score' | 'title' | 'exam_year' | 'word_count';
  sort_order?: 'asc' | 'desc';
  essay_type?: string;
  essay_style?: string;
  grade_level?: string;
  exam_year?: number;
  exam_region?: string;
  min_score?: number;
  max_score?: number;
}): Promise<PortfolioListResponse> => {
  const response = await api.get('/list', { params });
  return response.data;
};

// 获取作品详情
export const getPortfolioItem = async (
  itemId: string
): Promise<{ success: boolean; item: PortfolioItem }> => {
  const response = await api.get(`/${itemId}`);
  return response.data;
};

// 更新作品信息
export const updatePortfolioItem = async (
  itemId: string,
  data: {
    title?: string;
    tags?: string[];
    notes?: string;
    starred?: boolean;
    metadata?: Record<string, any>;
  }
): Promise<{ success: boolean; item: PortfolioItem }> => {
  const response = await api.patch(`/${itemId}`, data);
  return response.data;
};

// 删除作品
export const deletePortfolioItem = async (
  itemId: string
): Promise<{ success: boolean; message: string }> => {
  const response = await api.delete(`/${itemId}`);
  return response.data;
};

// 切换星标状态
export const toggleStar = async (
  itemId: string
): Promise<{ success: boolean; starred: boolean }> => {
  const response = await api.post(`/${itemId}/toggle-star`);
  return response.data;
};

// 添加标签
export const addTag = async (
  itemId: string,
  tag: string
): Promise<{ success: boolean; tags: string[] }> => {
  const response = await api.post(`/${itemId}/add-tag`, { tag });
  return response.data;
};

// 删除标签
export const removeTag = async (
  itemId: string,
  tag: string
): Promise<{ success: boolean; tags: string[] }> => {
  const response = await api.delete(`/${itemId}/remove-tag/${tag}`);
  return response.data;
};

// 获取所有标签
export const getAllTags = async (): Promise<{
  success: boolean;
  tags: TagInfo[];
}> => {
  const response = await api.get('/tags');
  return response.data;
};

// 批量删除
export const batchDelete = async (
  itemIds: string[]
): Promise<{ success: boolean; deleted: number; errors: any[] }> => {
  const response = await api.post('/batch-delete', { item_ids: itemIds });
  return response.data;
};

// 获取统计信息
export const getPortfolioStats = async (): Promise<{
  success: boolean;
  stats: PortfolioStats;
}> => {
  const response = await api.get('/stats');
  return response.data;
};

// 重置作品集
export const resetPortfolio = async (): Promise<{
  success: boolean;
  deleted: number;
  errors: any[];
}> => {
  const response = await api.delete('/reset');
  return response.data;
};
