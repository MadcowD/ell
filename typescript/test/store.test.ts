import { SQLiteStore } from '../src/serialize/sql'
import * as fs from 'fs'
import * as path from 'path'
import { LMPType } from '../src/lmp/types'
import { test, expect, beforeAll, afterAll, describe } from 'vitest'

let store: SQLiteStore

beforeAll(async () => {
  store = new SQLiteStore(':memory:')
  await store.initialize()
})


const testLmp = {
  lmp_id: 'test-lmp-1',
  name: 'TestLMP',
  source: 'console.log("Hello, World!");',
  dependencies: '{}',
  created_at: new Date(),
  lmp_type: LMPType.LM,
  api_params: {},
  initial_free_vars: {},
  initial_global_vars: {},
  num_invocations: 0,
  commit_message: 'Initial commit',
  version_number: 1,
  invocations: [],
  used_by: [],
  uses: [],
}

const testInvocation = {
  id: 'test-invocation-1',
  lmp_id: 'test-lmp-1',
  latency_ms: 100,
  prompt_tokens: 10,
  completion_tokens: 20,
  state_cache_key: 'test-cache-key',
  created_at: new Date().toISOString(),
  used_by_id: '',
  lmp: testLmp,
  consumed_by: [],
  consumes: [],
  used_by: null,
  uses: [],
  contents: {
    invocation_id: 'test-invocation-1',
    params: {},
    results: 'Hello, World!',
    invocation_api_params: {},
    global_vars: {},
    free_vars: {},
    is_external: false,
    invocation: {} as any, // This is a circular reference, so we're using `as any` for simplicity
  },
}

test('writeLmpAsync and getVersionsByFqnAsync', async () => {
  await store.writeLmpAsync(testLmp, {})
  const versions = await store.getVersionsByFqnAsync(testLmp.name)
  expect(versions.length).toBe(1)
  expect(versions[0].lmp_id).toBe(testLmp.lmp_id)
})

test('writeInvocationAsync', async () => {
  await store.writeInvocationAsync(testInvocation, new Set())
})
