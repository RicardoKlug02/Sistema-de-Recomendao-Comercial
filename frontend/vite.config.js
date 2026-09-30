import react from '@vitejs/plugin-react'
import { defineConfig, loadEnv } from 'vite'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, '.', 'VITE_')
  return {
    plugins: [react()],
    server: {
      proxy: {
        // Opcional em desenvolvimento: permite conferir a interface contra a API publicada.
        // A compilação continua usando a mesma origem, como exige o deploy atual da main.
        '/api': {
          target: env.VITE_PROXY_TARGET || 'http://127.0.0.1:8000',
          changeOrigin: true,
          proxyTimeout: 180000,
        },
      },
    },
  }
})
