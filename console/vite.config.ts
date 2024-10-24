import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vuetify from 'vite-plugin-vuetify'
import AutoImport from 'unplugin-auto-import/vite'
import { Options } from 'unplugin-auto-import/types'

const autoImports: Options = {
  dts: 'src/auto-imports.d.ts',
  vueTemplate: true,
  dirs: ['src/components'],
  imports: [
    'vue',
    'vue-router',
    { '@/axios': [['default', 'axios']] },
    { '@/stores/notifications': [['default', 'useNotifications']] },
    { '@/stores/messages': [['default', 'useMessages']] }
  ]
}

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [vue(), vuetify(), AutoImport(autoImports)],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  build: {
    sourcemap: true,
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
  },
  server: {
    proxy: {
      '/api': {
        target: 'https://localhost:7052',
        changeOrigin: true,
        secure: false,
        ws: true
      }
    }
  }
})
