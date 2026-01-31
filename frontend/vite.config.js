import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig(({ mode }) => {
  const isMockMode = mode === 'mock'
  
  return {
    plugins: [react()],
    server: {
      port: 5173,
      // Only proxy in non-mock mode
      ...(isMockMode ? {} : {
        proxy: {
          '/api': {
            target: 'http://localhost:8000',
            changeOrigin: true
          }
        }
      })
    }
  }
})
