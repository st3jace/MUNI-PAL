/**
 * Vite config — Healthcare CFO Landing Page
 *
 * Builds a standalone SPA for muni-pal.io.
 * Contains the healthcare landing page + MIR tools flow.
 *
 * Build:   npx vite build --config vite.config.healthcare.ts
 * Preview: npx vite preview --config vite.config.healthcare.ts
 * Dev:     npx vite --config vite.config.healthcare.ts
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
        input: 'index.healthcare.html',
      },
      outDir: 'dist-healthcare',
      emptyOutDir: true,
      sourcemap: false,
      minify: 'esbuild',
    },

    server: {
      port: 3003,
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
