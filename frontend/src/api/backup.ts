/**
 * 数据备份和导出 API
 */

import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:5000/backup',
  timeout: 60000,
});

// 备份数据库
export const backupDatabase = async (backupName?: string): Promise<{
  success: boolean;
  message: string;
  backup_path: string;
  backup_name: string;
  size_mb: number;
  timestamp: string;
  collections?: Array<{name: string; document_count: number}>;
  total_collections?: number;
}> => {
  const response = await api.post('/database', { backup_name: backupName });
  return response.data;
};

// 列出备份
export const listBackups = async (): Promise<{
  success: boolean;
  backups: Array<{
    name: string;
    path: string;
    size_mb: number;
    created_at: string;
    collections?: Array<{name: string; document_count: number}>;
    total_collections?: number;
  }>;
  total: number;
}> => {
  const response = await api.get('/list');
  return response.data;
};

// 删除备份
export const deleteBackup = async (backupName: string): Promise<{
  success: boolean;
  message: string;
}> => {
  const response = await api.delete(`/delete/${backupName}`);
  return response.data;
};

// 恢复备份
export const restoreBackup = async (backupName: string): Promise<{
  success: boolean;
  message: string;
  collections?: Array<{name: string; document_count: number}>;
  total_collections?: number;
  warning?: string;
}> => {
  const response = await api.post(`/restore/${backupName}`);
  return response.data;
};

// 导出对话记录
export const exportConversation = async (taskId?: string, format: 'markdown' | 'json' = 'markdown'): Promise<void> => {
  const response = await api.post('/export-conversation', {
    task_id: taskId,
    output_format: format,
  }, {
    responseType: format === 'markdown' ? 'blob' : 'json',
  });
  
  if (format === 'markdown') {
    // 触发文件下载
    const blob = new Blob([response.data], { type: 'text/markdown' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    
    // 从 Content-Disposition 或生成文件名
    const contentDisposition = response.headers['content-disposition'];
    let filename = 'conversation.md';
    if (contentDisposition) {
      const match = contentDisposition.match(/filename="?([^"]+)"?/);
      if (match) {
        filename = match[1];
      }
    }
    
    link.setAttribute('download', filename);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  }
};
