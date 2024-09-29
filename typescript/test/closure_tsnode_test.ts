import OpenAI from 'openai'
import { config } from '../src/configurator'
import { hello } from './fixtures/hello_world'
import * as logger from '../src/_logger'
import * as ell from 'ell-ai'

// logger.setGlobalLevel(logger.LogLevel.DEBUG)
ell.init({ store: '../logdir', verbose: true })

// beforeAll(() => {
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
  }
}

require('../examples/multi_lmp')

return

;(async () => {
  const result = await hello('sama')
  console.log(result)
})()
