import * as logging from '../src/util/_logging'
logging.setGlobalLevel(logging.LogLevel.DEBUG)
import { test, beforeEach } from 'mocha'
import OpenAI from 'openai'
import { config } from '../src/configurator'
import { Message } from '../src/types'
import { complex, simple } from 'ell-ai'
import assert from 'assert'
import {chatCompletionsToStream} from "./util";



describe('lmp', () => {
  beforeEach(() => {
    config.defaultClient = config.defaultClient || new OpenAI({ apiKey: 'test' })
    // @ts-expect-error
    config.defaultClient.chat.completions.create = async (...args) => {
      return chatCompletionsToStream([<OpenAI.Chat.Completions.ChatCompletion>{
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
      }])
    }
  })

  test('runtime', async () => {
    const child = simple({ model: 'gpt-4o-mini' }, async (a: string) => {
      return 'child'
    })
    const hello = simple({ model: 'gpt-4o' }, async (a: { a: string }) => {
      const ok = await child(a.a)
      return a.a + ok
    })

    const result = await hello({ a: 'world' })

    assert.equal(result, 'worldchild')

    assert.ok(hello.__ell_lmp_id__?.startsWith('lmp-'))
    assert.equal(hello.__ell_lmp_name__, 'hello')

    assert.ok(child.__ell_lmp_id__?.startsWith('lmp-'))
    assert.equal(child.__ell_lmp_name__, 'child')
  })

  test('complex', async () => {
    const child2 = complex({ model: 'gpt-4o-mini' }, async (a: string) => [new Message('assistant', 'child')])
    const result = await child2('world')
    assert.deepStrictEqual(result, new Message('assistant', 'child'))
  })
})
