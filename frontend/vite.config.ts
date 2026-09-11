import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import { loadEnv } from 'vite'

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, '.', '')
  const apiProxyTarget = env.VITE_API_PROXY_TARGET || 'http://127.0.0.1:8000'
  const advisorProxyTarget = env.VITE_ADVISOR_PROXY_TARGET || 'http://127.0.0.1:8300'
  const previewAllowedHost = env.VITE_PREVIEW_ALLOWED_HOST?.trim()

  const proxy = {
    '/api': {
      target: apiProxyTarget,
      changeOrigin: true,
    },
    '/advisor-api': {
      target: advisorProxyTarget,
      changeOrigin: true,
      rewrite: (path: string) => path.replace(/^\/advisor-api/, ''),
    },
  }

  return {
    plugins: [react()],
    test: {
      environment: 'jsdom',
      globals: true,
      setupFiles: './src/test/setup.ts',
    },
    server: {
      port: 3001,
      proxy,
    },
    preview: {
      port: 3001,
      proxy,
      allowedHosts: previewAllowedHost ? [previewAllowedHost] : [],
    },
  }
})
