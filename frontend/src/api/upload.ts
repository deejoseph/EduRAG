import apiClient from './client';

/** 单个文件导入结果 */
export interface FileImportResult {
  filename: string;
  status: 'success' | 'error';
  chunks: number;
  text_length?: number;
  title?: string;
  error?: string;
}

/** 上传响应 */
export interface UploadResponse {
  success: boolean;
  results: FileImportResult[];
  total_files: number;
  success_count: number;
  total_chunks: number;
  collection: string;
}

export const uploadApi = {
  /** 上传文件到知识库 */
  uploadFiles: (
    files: File[],
    collection: string = 'chinese_essays',
    onProgress?: (progressEvent: any) => void,
  ) => {
    const formData = new FormData();
    files.forEach(f => formData.append('files', f));
    formData.append('collection', collection);

    return apiClient.post<any, UploadResponse>(
      '/upload/files',
      formData,
      {
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 600000, // 上传+导入可能耗时较长，10分钟超时
        onUploadProgress: onProgress,
      },
    );
  },

  /** 删除集合 */
  deleteCollection: (name: string) =>
    apiClient.delete<any, { success: boolean; message: string }>(
      `/upload/collections/${name}`,
    ),
};
