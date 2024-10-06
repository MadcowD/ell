import { Message } from './types'
import { Tool } from './types/tools'

// todo. remove
export interface APICallResult {
  response: any
  actualStreaming: boolean
  actualN: number
  finalCallParams: Record<string, any>
}

export type EllCallParams = {
  /**
   * The model to use for the API call.
   */
  model: string

  /**
   * The messages to use for the API call.
   */
  messages: Message[]

  /**
   * The client to use for the API call.
   */
  client: any

  /**
   * The tools to use for the API call.
   */
  tools?: Tool<any, any>[]

  /**
   * The API parameters to use for the API call.
   */
  apiParams: Record<string, any>
}

export type Metadata = Record<string, any>

type ProviderCallFunction = (...args: any[]) => Promise<any>

/**
 * Abstract base class for all providers. Providers are API interfaces to language models, not necessarily API providers.
 * For example, the OpenAI provider is an API interface to OpenAI's API but also to Ollama and Azure OpenAI.
 * In Ell. We hate abstractions. The only reason this exists is to help implementers to implement their own provider correctly :)
 */
export interface Provider {
  dangerous_disable_validation: boolean

  /**
   * Implement this method to return the function that makes the API call to the language model.
   * For example, if you're implementing the OpenAI provider, you would return the function that makes the API call to OpenAI's API.
   * The function returned may be a function of the inputs (api_call_params).
   * For example, with the OpenAI provider, chat.completions.beta.parse for structured outputs
   * vs chat.completions for unstructred outputs.
   */
  providerCallFunction(client: any, api_call_params: Record<string, any>): ProviderCallFunction

  /**
   * Returns a list of disallowed call params that ell will override.
   */
  disallowedApiParams(): ReadonlySet<string>

  /**
   * Returns a list of available call params for the provider.
   */
  availableApiParams(client: any, api_call_params: Record<string, any>): string[]

  /**
   * Translate the ell call to provider call params.
   */
  translateToProvider(ell_call: EllCallParams): Promise<Record<string, any>>

  /**
   * Translate the provider response to ell format.
   */
  translateFromProvider(
    provider_response: any,
    ell_call: EllCallParams,
    provider_call_params: Record<string, any>,
    origin_id?: string,
    logger?: any
  ): Promise<[Message[], Metadata]>

  /**
   * Make the API call to the language model and return the result along with actual streaming, n values, and final call parameters.
   */
  call(ell_call: EllCallParams, origin_id?: string, logger?: any): Promise<[Message[], Record<string, any>, Metadata]>
}

export class BaseProvider implements Provider {
  dangerous_disable_validation = false

  disallowedApiParams(): ReadonlySet<string> {
    return new Set(['messages', 'tools', 'model', 'stream', 'stream_options'])
  }

  // todo. Python inspects the function parameters at runtime
  availableApiParams(client: any, api_call_params: Record<string, any>): string[] {
    // The set difference of the api_call_params and the disallowed api params
    return Object.keys(api_call_params).filter((key) => !this.disallowedApiParams().has(key))
  }

  translateToProvider(ell_call: any): Promise<Record<string, any>> {
    throw new Error('Method not implemented.')
  }

  translateFromProvider(
    provider_response: any,
    ell_call: EllCallParams,
    provider_call_params: Record<string, any>,
    origin_id?: string,
    logger?: any
  ): Promise<[Message[], Metadata]> {
    throw new Error('Method not implemented.')
  }

  providerCallFunction(
    client: any,
    api_call_params: Record<string, any>
  ): (api_call_params: Record<string, any>) => Promise<any> {
    throw new Error('Method not implemented.')
  }

  async call(
    ell_call: EllCallParams,
    origin_id: string,
    logger?: any
  ): Promise<[Message[], Record<string, any>, Metadata]> {
    const final_api_call_params = this.translateToProvider(ell_call)

    const provider_call_function = this.providerCallFunction(ell_call.client, final_api_call_params)

    const provider_resp = await provider_call_function(final_api_call_params)

    const [messages, metadata] = await this.translateFromProvider(
      provider_resp,
      ell_call,
      final_api_call_params,
      origin_id,
      logger
    )

    return [messages, final_api_call_params, metadata]
  }
}
