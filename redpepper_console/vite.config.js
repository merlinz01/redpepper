import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (id.includes('node_modules')) {
            let res = id.toString().split('node_modules/')[1].split('/')[0].toString()
            if (res == 'vue') {
              // vue results in an empty chunk
              return
            }
            return res
          }
        }
      }
    }
  }
})
