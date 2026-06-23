import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    // API 调用已改为直接请求后端 (http://localhost:5000)
    // 只保留不与前端路由冲突的代理规则
    proxy: {
      // 后端返回的音频文件 URL 是相对路径，需要代理
      '/podcast-audio': {
        target: 'http://localhost:5000',
        changeOrigin: true,
      },
    },
  },
})
