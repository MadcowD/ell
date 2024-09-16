import { defineConfig } from 'vitest/config'

export default defineConfig({
  test: {
    environment: 'node',
    env: {
      OPENAI_API_KEY: 'sk-proj-1234567890'
    }
  },
  build: {
    sourcemap: true,

  }
})