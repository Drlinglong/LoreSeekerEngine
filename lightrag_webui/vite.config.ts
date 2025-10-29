import { defineConfig } from 'vite'
import path from 'path'
import { webuiPrefix } from './src/lib/constants'
import react from '@vitejs/plugin-react-swc'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src')
    }
  },
  // base: process.env.VITE_BASE_URL || '/webui/',
  base: webuiPrefix,
  build: {
    outDir: path.resolve(__dirname, '../lightrag/api/webui'),
    emptyOutDir: true,
    chunkSizeWarningLimit: 3800,
    rollupOptions: {
      // Let Vite handle chunking automatically to avoid circular dependency issues
      output: {
        // Ensure consistent chunk naming format
        chunkFileNames: 'assets/[name]-[hash].js',
        // Entry file naming format
        entryFileNames: 'assets/[name]-[hash].js',
        // Asset file naming format
        assetFileNames: 'assets/[name]-[hash].[ext]'
      }
    }
  },
  server: {
    proxy: process.env.VITE_API_PROXY === 'true' && process.env.VITE_API_ENDPOINTS ?
      Object.fromEntries(
        process.env.VITE_API_ENDPOINTS.split(',').map(endpoint => [
          endpoint,
          {
            target: process.env.VITE_BACKEND_URL || 'http://localhost:9621',
            changeOrigin: true,
            rewrite: endpoint === '/api' ?
              (path) => path.replace(/^\/api/, '') :
              endpoint === '/docs' || endpoint === '/redoc' || endpoint === '/openapi.json' ?
                (path) => path : undefined
          }
        ])
      ) : {}
  }
})
