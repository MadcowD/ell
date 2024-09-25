import { SQLiteStore, WriteInvocationInput, WriteLMPInput } from '../src/serialize/sql'
import { LMPType } from '../src/lmp/types'
import { test, expect, beforeAll } from 'vitest'

let store: SQLiteStore

beforeAll(async () => {
  store = new SQLiteStore(':memory:')
  await store.initialize()
})

const testLmp: WriteLMPInput = {
  lmp_id: 'test-lmp-1',
  name: 'TestLMP',
  source: 'console.log("Hello, World!");',
  dependencies: '{}',
  language: 'typescript' as const,
  created_at: new Date().toISOString(),
  lmp_type: LMPType.LM,
  api_params: {},
  initial_free_vars: {},
  initial_global_vars: {},
  commit_message: 'Initial commit',
  version_number: 1,
  uses: [],
}

const testInvocation: WriteInvocationInput = {
  id: 'test-invocation-1',
  lmp_id: 'test-lmp-1',
  latency_ms: 100,
  prompt_tokens: 10,
  completion_tokens: 20,
  state_cache_key: 'test-cache-key',
  created_at: new Date().toISOString(),
  used_by_id: '',
  consumes: [],
  contents: {
    params: {},
    results: 'Hello, World!',
    invocation_api_params: {},
    global_vars: {},
    free_vars: {},
    is_external: false,
  },
}

test('writeLMP and getVersionsByFqn', async () => {
  await store.writeLMP(testLmp)
  const versions = await store.getVersionsByFqn(testLmp.name)
  expect(versions.length).toBe(1)
  expect(versions[0].lmp_id).toBe(testLmp.lmp_id)
})

test('writeInvocation', async () => {
  await store.writeInvocation(testInvocation)
})
