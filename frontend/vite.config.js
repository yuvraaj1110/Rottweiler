import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    strictPort: true,
    // Proxy API calls to the local FastAPI backend during development
    proxy: {
      '/process-video': 'http://localhost:8000',
      '/log-event': 'http://localhost:8000',
      '/logs': 'http://localhost:8000',
      '/clips': 'http://localhost:8000',
    },
  },
  preview: {
    port: 3000,
    strictPort: true,
  },
});