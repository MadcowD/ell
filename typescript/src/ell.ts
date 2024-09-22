import * as sourceMapSupport from 'source-map-support'
sourceMapSupport.install()

import './providers/openai'
import './models/openai'

import { AsyncLocalStorage } from 'async_hooks'
import { callsites } from './callsites'
import { EllTSC, LMP } from './tsc'
import { generateFunctionHash, generateInvocationId } from './hash'
import { config } from './configurator'
import { Message } from './types'
import { APICallResult } from './provider'
import {
  modelUsageLoggerPostEnd,
  modelUsageLoggerPostIntermediate,
  modelUsageLoggerPostStart,
  modelUsageLoggerPre,
} from './verbosity'
import { Logger } from '../_logger'

const logger = new Logger('ell')

type Kwargs = {
  // The name or identifier of the language model to use.
  model: string
  // An optional OpenAI client instance.
  client?: any //OpenAI
  // A list of tool functions that can be used by the LLM.
  tools?: any[]
  // If True, the LMP usage won't be tracked.
  exempt_from_tracking?: boolean
  // Additional API parameters
  [key: string]: any
}

type F = (...args: any[]) => Promise<string | Array<Message>>

type InvocationContents = {
  invocation_id: any
  params: any
  results: any
  invocation_api_params: any
}

type Invocation = {
  id: string
  lmp_id: string
  latency_ms: number
  prompt_tokens: number
  completion_tokens: number
  invocation_contents: InvocationContents
  used_by_id?: string
}

const tsc = new EllTSC()

// todo. storage
export let invocations: Invocation[] = []
export let lmps: LMP[] = []

/**
 * Used for tracing of invocations.
 * Uses AsyncLocalStorage.
 */
class InvocationContext {
  private storage: AsyncLocalStorage<Invocation[]>

  constructor() {
    this.storage = new AsyncLocalStorage<Invocation[]>()
  }

  async run<F extends (...args: any[]) => Promise<any>>(
    invocation: Invocation,
    callback: F
  ) {
    let stack = this.storage.getStore() || []
    stack = [...stack, invocation]
    return this.storage.run(stack, callback)
  }

  getCurrentInvocation(): Invocation | undefined {
    const stack = this.storage.getStore()
    return stack ? stack[stack.length - 1] : undefined
  }

  getParentInvocation(): Invocation | undefined {
    const stack = this.storage.getStore()
    return stack && stack.length > 1 ? stack[stack.length - 2] : undefined
  }
}

const getModelClient = async (args: Kwargs) => {
  if (args.client) {
    return args.client
  }
  const [client, _fallback] = config.getClientFor(args.model)
  return client
}

const invocationContext = new InvocationContext()
const writeInvocation = async (invocation: Invocation) => {
  invocations.push(invocation)
}

const writeLMP = async (lmp: LMP) => {
  lmps.push(lmp)
}

function getCallerFileLocation() {
  const callerSite = callsites()[2]
  let file = callerSite.getFileName()
  let line = callerSite.getLineNumber()
  let column = callerSite.getColumnNumber()
  if (file && line && column) {
    const mappedPosition = sourceMapSupport.mapSourcePosition({
      source: file,
      line: line,
      column: column,
    })
    file = mappedPosition.source
    line = mappedPosition.line
    column = mappedPosition.column
  }
  return { filepath: file, line, column }
}

const serializeLMP = async (args: LMP) => {
  try {
    // todo. commit message if not exists
    return await writeLMP(args)
  } catch (e) {
    logger.error(`Error serializing LMP: ${e}`)
  }
}

const convertMultimodalResponseToLstr = (response: Message[]) => {
  if (
    response.length === 1 &&
    response[0].content.length === 1 &&
    response[0].content[0].text
  ) {
    return response[0].content[0].text
  }
  return response
}
function convertMultimodalResponseToString(
  response: APICallResult['response']
): string | string[] {
  return Array.isArray(response)
    ? response.map((x) => x.content[0].text)
    : response.content[0].text
}

type SimpleLMPInner = (...args: any[]) => Promise<string | Array<Message>>
type SimpleLMP<A extends SimpleLMPInner> = ((
  ...args: Parameters<A>
) => Promise<string>) & {
  __ell_type__?: string
  __ell_lmp_name__?: string
  __ell_lmp_id__?: string | null
  __ell_invocation_id__?: string | null
}

/**
 * Invokes the LMP with tracking.
 * @param lmp I
 * @param args
 * @param f
 * @param a
 * @returns
 */
const invokeWithTracking = async (lmp: LMP, args: any[], f: F, a: Kwargs) => {
  const invocationId = generateInvocationId()
  return await invocationContext.run(
    // @ts-ignore
    {
      id: invocationId,
      lmp_id: lmp.lmpId,
    },
    async () => {
      await serializeLMP(lmp)
      const lmpfnoutput = await f(...args)
      const modelClient = await getModelClient(a)
      const provider = config.getProviderFor(modelClient)
      if (!provider) {
        throw new Error(`No provider found for model ${a.model} ${modelClient}`)
      }
      const messages =
        typeof lmpfnoutput === 'string'
          ? [new Message('user', lmpfnoutput)]
          : lmpfnoutput
      const apiParams = {
        // everything from a except tools
        ...a,
        tools: undefined,
      }
      if (config.verbose) {
        modelUsageLoggerPre(
          { ...lmp, name: lmp.lmpName },
          args,
          apiParams,
          lmp.lmpId,
          messages
        )
      }
      const callResult = await provider.callModel(
        modelClient,
        a.model,
        messages,
        apiParams,
        a.tools
      )
      if (config.verbose) {
        modelUsageLoggerPostStart(lmp.lmpId, callResult.actualN)
      }
      const postIntermediate = modelUsageLoggerPostIntermediate(
        lmp.lmpId,
        callResult.actualN
      )

      const [trackedResults, metadata] = await provider.processResponse(
        callResult,
        'todo',
        postIntermediate
      )
      if (config.verbose) {
        modelUsageLoggerPostEnd()
      }

      const result = convertMultimodalResponseToString(trackedResults[0])
      await writeInvocation({
        id: invocationId,
        lmp_id: lmp.lmpId,
        latency_ms: metadata.latency_ms,
        prompt_tokens: metadata.prompt_tokens,
        completion_tokens: metadata.completion_tokens,
        invocation_contents: {
          invocation_id: invocationId,
          params: args,
          results: result,
          invocation_api_params: a,
        },
        used_by_id: invocationContext.getParentInvocation()?.id,
      })
      return result
    }
  )
}

export const simple = <F extends SimpleLMPInner>(
  a: Kwargs,
  f: F
): SimpleLMP<F> => {
  const { filepath, line, column } = getCallerFileLocation()

  if (!filepath || !line || !column) {
    logger.error(
      `LMP cannot be tracked. Your source maps may be incorrect or unavailable.`
    )
  }

  let trackAttempted = false
  let lmp: LMP | undefined = undefined

  const wrapper: SimpleLMP<F> = async (...args: any[]) => {
    if (!wrapper.__ell_lmp_id__) {
      if (trackAttempted) {
        return f
      }
      trackAttempted = true
      lmp = await tsc.getLMP(filepath!, line!, column!)
      if (!lmp) {
        logger.error(
          `No LMP found at ${filepath}:${line}:${column}. Your source maps may be incorrect or unavailable.`
        )
      } else {
        const lmpId = generateFunctionHash(lmp.source, '', lmp.lmpName)
        lmp.lmpId = lmpId
      }
    }

    if (lmp && !a.exempt_from_tracking) {
      return await invokeWithTracking(lmp, args, f, a)
    }
    const lmpfnoutput = await f(...args)
    const modelClient = await getModelClient(a)
    const provider = config.getProviderFor(modelClient)
    if (!provider) {
      throw new Error(`No provider found for model ${a.model} ${modelClient}`)
    }
    const messages =
      typeof lmpfnoutput === 'string'
        ? [new Message('user', lmpfnoutput)]
        : lmpfnoutput
    const apiParams = {
      // everything from a except tools
      ...a,
      tools: undefined,
    }
    const callResult = await provider.callModel(
      modelClient,
      a.model,
      messages,
      apiParams,
      a.tools
    )
    const [trackedResults, metadata] = await provider.processResponse(
      callResult,
      'todo'
    )
    const result = convertMultimodalResponseToString(trackedResults[0])
    return result
  }

  wrapper.__ell_type__ = 'simple'
  Object.defineProperty(wrapper, '__ell_lmp_id__', {
    get: () => lmp?.lmpId,
  })
  Object.defineProperty(wrapper, '__ell_lmp_name__', {
    get: () => lmp?.lmpName,
  })

  return wrapper
}

export const complex = (a: Kwargs, f: F) => {
  const name = a.name

  const wrapper = async (...args: any[]) => {
    const { filepath, line, column } = getCallerFileLocation()
    await serializeLMP({ name, filepath, line, column })
    const result = await f(...args)
    await writeInvocation({
      id: generateInvocationId(),
      lmp_id: generateFunctionHash(filepath!, line!, column!),
      latency_ms: 0,
      prompt_tokens: 0,
      completion_tokens: 0,
      invocation_contents: {
        invocation_id: generateInvocationId(),
        params: args,
        invocation_api_params: a,
        results: result,
      },
    })
    exit()
    return result
  }
  return wrapper
}

import { init } from './configurator'
import { system, user } from './types/message'
export { init, config, system, user }
