import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/portfolio': {
        target: 'http://localhost:5000',
        changeOrigin: true,
      },
      '/hot-topics': {
        target: 'http://localhost:5000',
        changeOrigin: true,
      },
      '/writing': {
        target: 'http://localhost:5000',
        changeOrigin: true,
      },
      '/practice': {
        target: 'http://localhost:5000',
        changeOrigin: true,
      },
      '/search': {
        target: 'http://localhost:5000',
        changeOrigin: true,
      },
      '/upload': {
        target: 'http://localhost:5000',
        changeOrigin: true,
      },
      '/health': {
        target: 'http://localhost:5000',
        changeOrigin: true,
      },
      '/system': {
        target: 'http://localhost:5000',
        changeOrigin: true,
      },
      '/podcast-audio': {
        target: 'http://localhost:5000',
        changeOrigin: true,
      },
    },
  },
})
