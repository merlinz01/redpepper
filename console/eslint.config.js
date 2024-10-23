import { fileURLToPath } from 'node:url'
import { dirname } from 'node:path'
import { FlatCompat } from '@eslint/eslintrc'
import js from '@eslint/js'
import typescriptESLintParser from '@typescript-eslint/parser'
import pluginVue from 'eslint-plugin-vue'

const __filename = fileURLToPath(import.meta.url)
const __dirname = dirname(__filename)

const compat = new FlatCompat({
  baseDirectory: __dirname
})

export default [
  // Base configuration
  {
    linterOptions: {
      reportUnusedDisableDirectives: 'error'
    }
  },
  // JavaScript
  {
    ...js.configs.recommended,
    files: ['src/**/*.{js}']
  },
  // TypeScript
  ...compat.extends('plugin:@typescript-eslint/recommended').map((config) => {
    return {
      ...config,
      files: ['src/**/*.{ts,tsx}']
    }
  }),
  // Vue.js
  ...pluginVue.configs['flat/recommended'],
  // Prettier integration
  ...compat.extends('eslint-config-prettier'),
  // TypeScript for Vue
  {
    files: ['src/**/*.vue'],
    languageOptions: {
      parserOptions: {
        parser: typescriptESLintParser
      }
    }
  },
  // Rules overrides
  {
    rules: {
      'vue/attributes-order': 'off',
      'vue/valid-v-slot': [
        'error',
        {
          allowModifiers: true
        }
      ]
    }
  }
]
