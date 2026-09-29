import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// Encaminha chamadas locais à API publicada; nenhuma credencial fica no proxy.
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': {
        target: 'https://sistema-de-recomendao-comercial.onrender.com',
        changeOrigin: true,
        proxyTimeout: 180000,
      },
    },
  },
})
