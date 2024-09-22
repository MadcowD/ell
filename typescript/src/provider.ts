import { Message, LMP } from './types'

export interface APICallResult {
  response: any
  actualStreaming: boolean
  actualN: number
  finalCallParams: Record<string, any>
}

/**
 * Abstract base class for all providers. Providers are API interfaces to language models, not necessarily API providers.
 * For example, the OpenAI provider is an API interface to OpenAI's API but also to Ollama and Azure OpenAI.
 */
export interface Provider {
  /**
   * Make the API call to the language model and return the result along with actual streaming, n values, and final call parameters.
   */
  callModel(
    client: any,
    model: string,
    messages: any[],
    apiParams: Record<string, any>,
    tools?: LMP[]
  ): Promise<APICallResult>

  /**
   * Process the API response and convert it to ell format.
   */
  processResponse(
    callResult: APICallResult,
    _invocationOrigin: string,
    logger?: any,
    tools?: LMP[]
  ): Promise<[Message[], Record<string, any>]>

  /**
   * Check if the provider supports streaming.
   */
  supportsStreaming(): boolean

  /**
   * Return the type of client this provider supports.
   */
  getClientType(): any
}
