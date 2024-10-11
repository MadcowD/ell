import * as logging from '../src/util/_logging'
logging.setGlobalLevel(logging.LogLevel.DEBUG)
import { test, before } from 'mocha'
import OpenAI from 'openai'
import { config } from '../src/configurator'
import { Message } from '../src/types'
import { complex, tool } from 'ell-ai'
import assert from 'assert'

before(() => {
  config.defaultClient = config.defaultClient || new OpenAI({ apiKey: 'test' })
  // @ts-expect-error
  config.defaultClient.chat.completions.create = async (...args) => {
    return <OpenAI.Chat.Completions.ChatCompletion>{
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
          finish_reason: 'tool_calls',
          logprobs: null,
          message: {
            tool_calls: [
              {
                type: 'function',
                id: '123',
                function: { name: 'getWeather', arguments: JSON.stringify({ place: 'santa cruz' }) },
              },
            ],
          },
        },
      ],
    }
  }
})

test('tools', async () => {
  const getWeather = tool(
    async ({ place }: { place: string }) => {
      return `The weather in ${place} is pretty nice.`
    },
    {
      description: 'Get the weather in a given place',
      paramDescriptions: {
        place: 'The place to get the weather for',
      },
    }
  )
  const hello = complex({ model: 'gpt-4o', tools: [getWeather] }, async (place: string) => {
    return [new Message('user', `Can you tell me the weather in ${place}?`)]
  })

  const result = await hello('santa cruz')
  assert.equal(
    await result.callToolsAndCollectAsMessage().then((x) => x.toolResults?.[0]?.result.map((x) => x.text).join('')),
    '"The weather in santa cruz is pretty nice."'
  )


  // @ts-expect-error
  assert.ok(getWeather.__ell_lmp_id__?.startsWith('lmp-'))
  // @ts-expect-error
  assert.equal(getWeather.__ell_lmp_name__, 'getWeather')
})
