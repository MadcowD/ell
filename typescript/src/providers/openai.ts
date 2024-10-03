try {
  require('openai')
} catch (e) {
  console.error('OpenAI not found. Please install it to use the OpenAI provider.')
}
import { APICallResult, Provider } from '../provider'
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
import { zodResponseFormat } from 'openai/helpers/zod'
import { Tool } from '../types/tools'

class _lstr {
  constructor(
    public value: string,
    public _originTrace: string
  ) {}
}

class _OpenAIProvider implements Provider {
  contentBlockToOpenAIFormat(contentBlock: ContentBlock): any {
    if (contentBlock.image) {
      const base64Image = serializeImage(contentBlock.image)
      const imageUrl: any = { url: base64Image }

      if (contentBlock.image_detail) {
        imageUrl.detail = contentBlock.image_detail
      }

      return {
        type: 'image_url',
        image_url: imageUrl,
      }
    } else if (contentBlock.text) {
      return {
        type: 'text',
        text: contentBlock.text,
      }
    } else if (contentBlock.parsed) {
      return {
        type: 'text',
        text: contentBlock.parsed,
      }
    } else {
      return null
    }
  }

  messageToOpenAIFormat(message: Message): any {
    const openaiMessage: any = {
      role: message.toolResults ? 'tool' : message.role,
      content: message.content.map((c) => OpenAIProvider.contentBlockToOpenAIFormat(c)).filter(Boolean),
    }

    if (message.toolCalls?.length) {
      try {
        openaiMessage.tool_calls = message.toolCalls.map((toolCall) => ({
          id: toolCall.tool_call_id,
          type: 'function',
          function: {
            name: toolCall.tool.name,
            arguments: JSON.stringify(toolCall.params),
          },
        }))
        openaiMessage.content = null
      } catch (e) {
        console.error(`Error serializing tool calls: ${e}. Did you fully type your @ell.tool decorated functions?`)
        throw e
      }
    }

    if (message.toolResults?.length) {
      openaiMessage.tool_call_id = message.toolResults[0].tool_call_id
      openaiMessage.content = message.toolResults[0].result[0].text
      // Assertions omitted as TypeScript's type system should handle these checks
    }

    return openaiMessage
  }

  async callModel(
    client: OpenAI,
    model: string,
    messages: Message[],
    apiParams: any,
    tools?: Tool<any, any>[]
  ): Promise<APICallResult> {
    const finalCallParams = { ...apiParams }
    // todo. create a type that contains all ell params
    // put it in one place and provide a function that removes them, leaving
    // the api_params for the model
    delete finalCallParams.exempt_from_tracking
    const openaiMessages = messages.map((message) => OpenAIProvider.messageToOpenAIFormat(message))

    const actualN = apiParams.n || 1
    finalCallParams.model = model
    finalCallParams.messages = openaiMessages

    let response

    if (model === 'o1-preview' || model === 'o1-mini') {
      // Ensure no system messages are present
      if (finalCallParams.messages.some((msg: any) => msg.role === 'system')) {
        throw new Error('System messages are not allowed for o1-preview or o1-mini models')
      }

      response = await client.chat.completions.create(finalCallParams)
      delete finalCallParams.stream
      delete finalCallParams.stream_options
    } else if (finalCallParams.response_format) {
      delete finalCallParams.stream
      delete finalCallParams.stream_options
      const response_format = zodResponseFormat(finalCallParams.response_format, "mycooltype")
      response = await client.beta.chat.completions.parse({
        ...finalCallParams,
        response_format,
      })
    } else {
      if (tools) {
        finalCallParams.toolChoice = 'auto'
        finalCallParams.tools = tools.map((tool) => ({
          type: 'function',
          function: {
            name: tool.__ell_tool_name__,
            description: tool.__ell_tool_description__,
            parameters: tool.__ell_tool_input__,
          },
        }))
        delete finalCallParams.stream
        delete finalCallParams.stream_options
      } else {
        finalCallParams.stream_options = { include_usage: true }
        finalCallParams.stream = true
      }

      response = await client.chat.completions.create(finalCallParams)
    }

    return {
      response,
      // todo.
      actualStreaming: response instanceof OpenAIStream,
      actualN,
      finalCallParams,
    }
  }

  async processResponse(
    callResult: APICallResult,
    _invocationOrigin: string,
    logger?: (content: string, options: { isRefusal: boolean }) => void,
    tools?: Tool<any, any>[]
  ): Promise<[Message[], Record<string, any>]> {
    const choicesProgress: Record<number, any[]> = {}
    const apiParams = callResult.finalCallParams
    let metadata: Record<string, any> = {}

    const response = callResult.actualStreaming ? callResult.response : [callResult.response]

    for await (const chunk of response) {
      if (chunk.usage) {
        metadata = chunk.usage
        if (callResult.actualStreaming) continue
      }

      for (const choice of chunk.choices) {
        choicesProgress[choice.index] = choicesProgress[choice.index] || []
        choicesProgress[choice.index].push(choice)

        if (choice.index === 0 && logger) {
          logger(
            callResult.actualStreaming
              ? choice.delta.content || ''
              : choice.message.content || choice.message.refusal || '',
            {
              isRefusal: callResult.actualStreaming ? false : !!choice.message.refusal,
            }
          )
        }
      }
    }

    const trackedResults: Message[] = []

    for (const [_, choiceDeltas] of Object.entries(choicesProgress).sort((a, b) => Number(a[0]) - Number(b[0]))) {
      const content: ContentBlock[] = []

      if (callResult.actualStreaming) {
        const textContent = choiceDeltas.map((choice) => choice.delta.content || '').join('')

        if (textContent) {
          content.push(
            new ContentBlock({
              // TODO. lstr
              text: textContent,
              // text: new _lstr(textContent, { _originTrace: _invocationOrigin }),
            })
          )
        }
      } else {
        const choice = choiceDeltas[0].message
        if (choice.refusal) {
          throw new Error(choice.refusal)
        }
        if (apiParams.response_format) {
          content.push(new ContentBlock({ parsed: choice.parsed }))
        } else if (choice.content) {
          content.push(
            new ContentBlock({
              // TODO. lstr
              text: choice.content,
              // text: new _lstr(choice.content, { _originTrace: _invocationOrigin }),
            })
          )
        }

        if (choice.toolCalls?.length) {
          if (!tools?.length) {
            throw new Error(
              'Tools not provided, yet tool calls in response. Did you manually specify a tool spec without using ell.tool?'
            )
          }

          for (const toolCall of choice.toolCalls) {
            const matchingTool = tools.find((tool) => tool.name === toolCall.function.name) as InvocableTool | undefined
            if (matchingTool) {
              const params = new matchingTool.paramsModel(JSON.parse(toolCall.function.arguments))
              content.push(
                new ContentBlock({
                  tool_call: new ToolCall(
                    matchingTool,
                    // TODO. lstr
                    toolCall.id,
                    // new _lstr(toolCall.id, { _originTrace: _invocationOrigin }),
                    params
                  ),
                })
              )
            }
          }
        }
      }

      trackedResults.push(
        new Message(callResult.actualStreaming ? choiceDeltas[0].delta.role : choiceDeltas[0].message.role, content)
      )
    }

    return [trackedResults, metadata]
  }

  supportsStreaming(): boolean {
    return true
  }

  getClientType(): typeof OpenAI {
    return OpenAI
  }
}

const OpenAIProvider = new _OpenAIProvider()

registerProvider(OpenAIProvider)
