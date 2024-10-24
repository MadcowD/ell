import assert from 'assert'
import OpenAI from 'openai'
import { config } from '../src/configurator'
import { chatCompletionsToStream } from './util'
import { SQLiteStore } from '../src/serialize/sql'
import * as ell from 'ell-ai'

describe('tracing', () => {
  let store: SQLiteStore
  beforeEach(async () => {
    store = new SQLiteStore(':memory:')
    await store.initialize()
    ell.init({ store })

    config.defaultClient = config.defaultClient || new OpenAI({ apiKey: 'test' })
    // @ts-expect-error
    config.defaultClient.chat.completions.create = async (...args) => {
      return chatCompletionsToStream([
        <OpenAI.Chat.Completions.ChatCompletion>{
          usage: {
            prompt_tokens: 10,
            completion_tokens: 10,
            latency_ms: 10,
            total_tokens: 20,
          },
          id: 'chatcmpl-123',
          created: 1677652288,
          model: 'gpt-3.5-turbo-0125',
          object: 'chat.completion',
          choices: [
            <OpenAI.Chat.Completions.ChatCompletion.Choice>{
              index: 0,
              finish_reason: 'stop',
              logprobs: null,
              message: {
                // @ts-expect-error
                content: args[0].messages[0].content[0].text,
                role: 'assistant',
                refusal: null,
              },
            },
          ],
        },
      ])
    }
  })

  it('simple', async () => {
    const hello = require('./fixtures/hello_world')
    const result = await hello.hello('world')

    assert.equal(result, 'You are a helpful and expressive assistant.')

    const lmp = (await store.db?.all('SELECT * FROM serializedlmp'))?.[0]
    assert.ok(typeof lmp.created_at === 'string')
    delete lmp.created_at
    assert.deepEqual(lmp, {
      lmp_id: 'lmp-a79d4140040f36d6c8074901fd00d769',
      name: 'test.fixtures.hello_world.hello',
      source:
        'export const hello = ell.simple({ model: \'gpt-4o-mini\' }, (name: string) => {\n  const adjective = getRandomAdjective()\n  const punctuation = getRandomPunctuation()\n\n  return [\n    ell.system(\'You are a helpful and expressive assistant.\'),\n    ell.user(`Say a ${adjective} hello to ${name}${punctuation}`),\n  ] \n})',
      language: 'typescript',
      dependencies: '',
      lmp_type: 'LM',
      api_params: '{"model":"gpt-4o-mini"}',
      initial_free_vars: '{}',
      initial_global_vars: '{}',
      num_invocations: 1,
      commit_message: 'Initial version',
      version_number: 1,
    })

    const invocation = (await store.db?.all('SELECT * FROM invocation'))?.[0]
    const invocationId = invocation.id

    assert.ok(invocationId.startsWith('invocation-'))
    delete invocation.id
    assert.ok(typeof invocation.created_at === 'string')
    delete invocation.created_at
    assert.ok(typeof invocation.latency_ms === 'number')
    delete invocation.latency_ms

    assert.deepStrictEqual(invocation, {
      lmp_id: lmp.lmp_id,
      prompt_tokens: null,
      completion_tokens: null,
      state_cache_key: '',
      used_by_id: null,
    })

    const invocationContents = (await store.db?.all('SELECT * FROM invocationcontents'))?.[0]

    assert.equal(invocationContents?.invocation_id, invocationId)
    delete invocationContents.invocation_id

    // Free vars
    const freeVars = JSON.parse(invocationContents.free_vars)
    assert.deepEqual(freeVars.name, 'world')
    assert.ok(['enthusiastic', 'cheerful', 'warm', 'friendly', 'heartfelt', 'sincere'].includes(freeVars.adjective))
    assert.ok(['!', '!!', '!!!'].includes(freeVars.punctuation))
    delete invocationContents.free_vars

    // Global vars
    const globalVars = JSON.parse(invocationContents.global_vars)
    assert.deepEqual(globalVars, {})
    delete invocationContents.global_vars

    assert.deepStrictEqual(invocationContents, {
      'invocation_api_params': '{"model":"gpt-4o-mini"}',
      'is_external': 0,
      'params': '["world"]',
      'results': '"You are a helpful and expressive assistant."',
    })
  })
})
