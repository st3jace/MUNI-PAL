/**
 * Vite config — Readiness MVP (readiness.elaunchshop.com)
 *
 * Builds a standalone SPA with the readiness assessment as the hero.
 * Works fully client-side when the backend sensing API is unavailable.
 *
 * Build:   npx vite build --config vite.config.readiness.ts
 * Preview: npx vite preview --config vite.config.readiness.ts
 * Dev:     npx vite --config vite.config.readiness.ts
 */

import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, '.', '')
  const apiTarget = env.VITE_SENSING_API_URL || 'http://127.0.0.1:8000'

  return {
    plugins: [react()],

    build: {
      rollupOptions: {
        input: 'index.readiness.html',
      },
      outDir: 'dist-readiness',
      emptyOutDir: true,
      sourcemap: false,
      minify: 'esbuild',
    },

    server: {
      port: 3004,
      proxy: {
        '/api/v1/sensing': {
          target: apiTarget,
          changeOrigin: true,
        },
        '/health': {
          target: apiTarget,
          changeOrigin: true,
        },
      },
    },
  }
})
