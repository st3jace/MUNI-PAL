/**
 * Vite config — Sensing Microservice Frontend
 *
 * Builds a standalone SPA for muni-pal.io that contains only
 * the /tools/* sensing pages. Output goes to dist/ (served by Nginx).
 *
 * Build:  npx vite build --config vite.config.sensing.ts
 * Preview: npx vite preview --config vite.config.sensing.ts
 */

import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { loadEnv } from 'vite'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, '.', '')
  // In production the frontend is served from the same origin as the API.
  // Override with VITE_SENSING_API_URL to point at a different host.
  const apiTarget = env.VITE_SENSING_API_URL || 'http://sensing-api:8000'

  return {
    plugins: [react()],

    // Use sensing-specific entry point
    build: {
      rollupOptions: {
        input: 'index.sensing.html',
      },
      outDir: 'dist',
      emptyOutDir: true,
      sourcemap: false,
      minify: 'esbuild',
    },

    // Dev server — proxies to the sensing API only
    server: {
      port: 3002,
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
