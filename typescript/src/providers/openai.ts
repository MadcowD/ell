try {
  require('openai')
} catch (e) {
  console.error('OpenAI not found. Please install it to use the OpenAI provider.')
}
import { APICallResult, BaseProvider, EllCallParams, Metadata, Provider } from '../provider'
import { Message, ContentBlock, ToolCall } from '../types'
import { LMP } from '../types/message'
// import { serializeImage } from "../util/serialization";
import { config, registerProvider } from '../configurator'
import OpenAI from 'openai'
// TODO>
const serializeImage = (image: any) => {
  return image
  // return `data:image/jpeg;base64,${image.data}`;
}

import { Stream as OpenAIStream } from 'openai/streaming'
import { zodFunction, zodResponseFormat } from 'openai/helpers/zod'
import { Tool } from '../types/tools'
import { ZodAny, ZodType } from 'zod'
import * as logging from '../util/_logging'

const logger = logging.getLogger('openai-provider')

type OpenAIResponseFormat =
  | OpenAI.ResponseFormatText
  | OpenAI.ResponseFormatJSONObject
  | OpenAI.ResponseFormatJSONSchema

class _lstr {
  constructor(
    public value: string,
    public _originTrace: string
  ) {}
}

const mapResponseFormat = (responseFormat: unknown): OpenAIResponseFormat | undefined => {
  if (responseFormat instanceof ZodType) {
    return zodResponseFormat(responseFormat, 'ZodType')
  }

  // @ts-ignore we trust the user here for now
  return responseFormat
}

function omit<T extends object, K extends keyof T>(obj: T, keys: K[]): Omit<T, K> {
  const result = { ...obj }
  for (const key of keys) {
    delete result[key]
  }
  return result
}

const mapToolDefinition = (tool: Tool<any, any>): OpenAI.Chat.Completions.ChatCompletionTool => {
  if (tool.__ell_tool_input__ instanceof ZodType && tool.__ell_tool_output__ instanceof ZodType) {
    return zodFunction({
      name: tool.__ell_tool_name__,
      parameters: tool.__ell_tool_input__,
      description: tool.__ell_tool_description__,
      function: tool,
    })
  }

  throw new Error(`Unsupported tool definition for openai: ${tool}`)
}

const getCanStream = (ellCall: EllCallParams) => {
  if (ellCall.tools && ellCall.tools.length > 0) {
    return false
  }
  if (ellCall.apiParams.response_format) {
    return false
  }
  return true
}
const mapToStreamingParams = async (
  ellCall: EllCallParams
): Promise<OpenAI.Chat.Completions.ChatCompletionCreateParamsStreaming> => {
  const messages = await Promise.all(ellCall.messages.map((message) => messageToOpenAIFormat(message)))

  return {
    model: ellCall.model,
    ...omit(ellCall.apiParams, ['tools', 'response_format', 'messages', 'stream', 'stream_options']),
    messages,
    response_format: mapResponseFormat(ellCall.apiParams.response_format),
    stream: true,
    stream_options: { include_usage: true },
  }
}

const mapToNonStreamingParams = async (
  ellCall: EllCallParams
): Promise<OpenAI.Chat.Completions.ChatCompletionCreateParamsNonStreaming> => {
  const messages = await Promise.all(ellCall.messages.map((message) => messageToOpenAIFormat(message)))
  return {
    model: ellCall.model,
    messages,
    tool_choice: ellCall.tools && ellCall.tools.length > 0 ? 'auto' : undefined,
    tools: ellCall.tools?.map((tool) => mapToolDefinition(tool)),
    response_format: mapResponseFormat(ellCall.apiParams.response_format),
    ...omit(ellCall.apiParams, ['tools', 'response_format', 'messages', 'stream', 'stream_options']),
    stream: false,
  } as OpenAI.Chat.Completions.ChatCompletionCreateParamsNonStreaming
}

class _OpenAIProvider extends BaseProvider implements Provider {
  constructor() {
    super()
  }
  dangerous_disable_validation = true

  // TODO. needed?
  disallowedApiParams() {
    return new Set([])
  }
  // TODO. needed? types?
  availableApiParams(client: any, api_call_params: Record<string, any>): string[] {
    return []
  }

  // TODO. needed? only public api is "call"
  providerCallFunction(client: any, api_call_params: Record<string, any>): (...args: any[]) => Promise<any> {
    if (api_call_params.response_format) {
      return (...args: any[]) => client.beta.chat.completions.parse(...args)
    }
    return (...args: any[]) => client.chat.completions.create(...args)
  }

  async call(
    params: EllCallParams,
    origin_id: string,
    logger?: any
  ): Promise<[Message[], Record<string, any>, Metadata]> {
    const input = await this.translateToProvider(params)

    const callAPI = this.providerCallFunction(params.client, input)

    const output = await callAPI(input)

    const [messages, metadata] = await this.translateFromProvider(output, params, input, origin_id, logger)

    return [messages, input, metadata]
  }

  async translateToProvider(ellCall: EllCallParams): Promise<OpenAI.Chat.Completions.ChatCompletionCreateParams> {
    const canStream = getCanStream(ellCall)
    if (!canStream && ellCall.apiParams.stream) {
      // TODO. Should we let openai handle this?
      // maybe the user knows better than us (if openai adds support for these arguments)
      throw new Error(
        `Received stream:true api params, but may not be supported for ${ellCall.model} with ${ellCall.tools ? 'tools' : ''} ${ellCall.apiParams.response_format ? 'response_format' : ''}`
      )
    }
    if (canStream) {
      return await mapToStreamingParams(ellCall)
    } else {
      return await mapToNonStreamingParams(ellCall)
    }
  }

  async translateFromProvider(
    provider_response: any,
    ell_call: EllCallParams,
    provider_call_params: Record<string, any>,
    origin_id?: string,
    logger?: (content: string, options: { isRefusal: boolean }) => void
  ): Promise<[Message[], Metadata]> {
    const metadata: Metadata = {}
    const messages: Message[] = []
    const did_stream = provider_call_params.stream || false

    if (did_stream) {
      const message_streams: Record<number, any[]> = {}
      let role: string | undefined

      for await (const chunk of provider_response) {
        Object.assign(metadata, omit(chunk, ['choices']))

        for (const chat_compl_chunk of chunk.choices) {
          const index = chat_compl_chunk.index
          message_streams[index] = message_streams[index] || []
          message_streams[index].push(chat_compl_chunk)
          const delta = chat_compl_chunk.delta
          role = role || delta.role

          if (index === 0 && logger) {
            logger(delta.content || '', { isRefusal: delta.refusal || false })
          }
        }
      }

      for (const [_, message_stream] of Object.entries(message_streams).sort((a, b) => Number(a[0]) - Number(b[0]))) {
        const text = message_stream.map((choice) => choice.delta.content || '').join('')
        messages.push(
          new Message(role!, [
            new ContentBlock({
              text: text,
              // new _lstr(text, origin_id)
            }),
          ])
        )
      }
    } else {
      Object.assign(metadata, omit(provider_response, ['choices']))

      for (const oai_choice of provider_response.choices) {
        const role = oai_choice.message.role
        const content_blocks: ContentBlock[] = []
        const message = oai_choice.message

        if (message.refusal) {
          throw new Error(message.refusal)
        }

        if ('parsed' in message) {
          if (message.parsed) {
            content_blocks.push(new ContentBlock({ parsed: message.parsed }))
            if (logger) logger(JSON.stringify(message.parsed), { isRefusal: false })
          }
        } else {
          if (message.content) {
            content_blocks.push(
              new ContentBlock({
                text: message.content,
                // new _lstr(message.content, origin_id)
              })
            )
            if (logger) logger(message.content, { isRefusal: false })
          }

          if (message.tool_calls) {
            for (const tool_call of message.tool_calls) {
              const matching_tool = ell_call.tools?.find((tool) => tool.__ell_tool_name__ === tool_call.function.name)
              if (!matching_tool) {
                throw new Error('Model called tool not found in provided toolset.')
              }
              content_blocks.push(
                new ContentBlock({
                  tool_call: new ToolCall(
                    matching_tool,
                    tool_call.id,
                    //new _lstr(tool_call.id, origin_id),
                    JSON.parse(tool_call.function.arguments)
                  ),
                })
              )
              if (logger) logger(JSON.stringify(tool_call), { isRefusal: false })
            }
          }
        }

        messages.push(new Message(role, content_blocks))
      }
    }

    return [messages, metadata]
  }
}

const OpenAIProvider = new _OpenAIProvider()

registerProvider(OpenAIProvider, OpenAI)

export const contentBlockToOpenAIFormat = async (
  contentBlock: ContentBlock
): Promise<OpenAI.Chat.Completions.ChatCompletionContentPart> => {
  if (contentBlock.image) {
    const base64Image = await contentBlock.image.serialize()
    return {
      type: 'image_url',
      image_url: { url: base64Image, detail: contentBlock.image.detail },
    } as OpenAI.Chat.Completions.ChatCompletionContentPartImage
  } else if (contentBlock.text) {
    return {
      type: 'text',
      text: contentBlock.text,
    }
  } else if (contentBlock.parsed) {
    return {
      type: 'text',
      text: JSON.stringify(contentBlock.parsed),
    }
  } else {
    throw new Error(`Unsupported content block type for openai: ${contentBlock}`)
  }
}

export const messageToOpenAIFormat = async (
  message: Message
): Promise<OpenAI.Chat.Completions.ChatCompletionMessageParam> => {
  if (message.toolCalls?.length) {
    try {
      if (message.role !== 'assistant') {
        throw new Error('Tool calls must be from the assistant.')
      }
      return {
        role: 'assistant',
        tool_calls: message.toolCalls.map((toolCall) => ({
          id: toolCall.tool_call_id!,
          type: 'function',
          function: {
            name: toolCall.tool.name,
            arguments: JSON.stringify(toolCall.params),
          },
        })),
      }
    } catch (e) {
      console.error(`Error serializing tool calls: ${e}. Did you fully type your @ell.tool decorated functions?`)
      throw e
    }
  }
  if (message.toolResults?.length) {
    return {
      role: 'tool' as const,
      tool_call_id: message.toolResults[0].tool_call_id,
      // @ts-ignore may be undefined
      content: message.toolResults[0].result[0].text!,
    }
  }

  // @ts-ignore
  const openaiMessage:
    | OpenAI.Chat.Completions.ChatCompletionSystemMessageParam
    | OpenAI.Chat.Completions.ChatCompletionUserMessageParam
    | OpenAI.Chat.Completions.ChatCompletionAssistantMessageParam = {
    role: message.role as 'user' | 'assistant' | 'system',
    content: await Promise.all(message.content.map((c) => contentBlockToOpenAIFormat(c))),
  }

  return openaiMessage
}
