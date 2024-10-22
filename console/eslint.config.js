import { fileURLToPath } from 'node:url'
import { dirname } from 'node:path'
import { FlatCompat } from '@eslint/eslintrc'
import js from '@eslint/js'
import typescriptESLintParser from '@typescript-eslint/parser'

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
  ...compat.extends('plugin:vue/vue3-recommended').map((config) => {
    return {
      ...config,
      files: ['src/**/*.vue'],
      languageOptions: {
        ...config.languageOptions,
        parserOptions: {
          ...config.languageOptions?.parserOptions,
          parser: typescriptESLintParser
        }
      }
    }
  }),
  // Prettier integration
  ...compat.extends('eslint-config-prettier'),
  // Rules overrides
  {
    rules: {
      'vue/attributes-order': 'off'
    }
  }
]
