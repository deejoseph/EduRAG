import axios from 'axios';
import { message } from 'antd';

const apiClient = axios.create({
  baseURL: 'http://localhost:5000',
  timeout: 120000, // LLM 推理较慢，超时 120 秒
  headers: { 'Content-Type': 'application/json' },
});

// 响应拦截器：统一提取 data、处理错误
apiClient.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const msg = error.response?.data?.error || error.message || '请求失败';
    message.error(msg, 5);
    return Promise.reject(error);
  }
);

export default apiClient;
