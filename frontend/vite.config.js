import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import { loadEnv } from 'vite';
// https://vitejs.dev/config/
export default defineConfig(function (_a) {
    var mode = _a.mode;
    var env = loadEnv(mode, '.', '');
    var apiProxyTarget = env.VITE_API_PROXY_TARGET || 'http://127.0.0.1:8000';
    var advisorProxyTarget = env.VITE_ADVISOR_PROXY_TARGET || 'http://127.0.0.1:8300';
    return {
        plugins: [react()],
        test: {
            environment: 'jsdom',
            globals: true,
            setupFiles: './src/test/setup.ts',
        },
        server: {
            port: 3001,
            proxy: {
                '/api': {
                    target: apiProxyTarget,
                    changeOrigin: true,
                },
                '/advisor-api': {
                    target: advisorProxyTarget,
                    changeOrigin: true,
                    rewrite: function (path) { return path.replace(/^\/advisor-api/, ''); },
                },
            },
        },
    };
});
