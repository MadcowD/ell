import * as sourceMapSupport from 'source-map-support'
sourceMapSupport.install()

import './providers/openai'
import './models/openai'

import { AsyncLocalStorage } from 'async_hooks'
import { callsites } from './callsites'
import { EllTSC, LMPDefinition, LMPDefinitionType } from './tsc'
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
import { Logger } from './_logger'
import { performance } from 'perf_hooks'
import * as inspector from 'inspector/promises'
import * as sm from 'source-map'
import {
  extractSourceMapUrl,
  getBestClosureInspectionBreakpoint,
  getSourceMapJSON,
  resolveScriptIdToFile,
} from './closure'
import { WriteInvocationInput, WriteLMPInput } from './serialize/sql'
import { ToolFunction } from './types/tools'
import { LMPType } from './lmp/types'

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

/**
 * Used for tracing of invocations.
 * Uses AsyncLocalStorage.
 */
class InvocationContext {
  private storage: AsyncLocalStorage<Invocation[]>

  constructor() {
    this.storage = new AsyncLocalStorage<Invocation[]>()
  }

  async run<F extends (...args: any[]) => Promise<any>>(invocation: Invocation, callback: F) {
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

const serializeLMP = async (args: Omit<WriteLMPInput, 'commit_message' | 'version_number'>) => {
  try {
    const serializer = config.getStore()
    if (!serializer) {
      return
    }
    // todo. see if we can defer some of these responsibilities to the serializer/backend
    // for now we'll get things working the same as python
    // todo. we need to come up with a fully qualified name
    const otherVersions = await serializer.getVersionsByFqn(args.name)
    if (otherVersions.length === 0) {
      // We are the first version of the LMP!

      return await serializer.writeLMP({
        ...args,
        commit_message: 'Initial version',
        version_number: 1,
      })
    }

    const newVersionNumber = otherVersions[0].version_number + 1
    return await serializer.writeLMP({
      ...args,
      // TODO. check if auto commit and create a commit message if so
      commit_message: 'New version',
      version_number: newVersionNumber,
    })
  } catch (e) {
    logger.error(`Error serializing LMP: ${e}`)
  }
}

const serializeInvocation = async (input: WriteInvocationInput) => {
  try {
    const serializer = config.getStore()
    if (!serializer) {
      return
    }
    return await serializer.writeInvocation(input)
  } catch (e) {
    logger.error(`Error serializing invocation: ${e}`)
  }
}

const convertMultimodalResponseToLstr = (response: Message[]) => {
  if (response.length === 1 && response[0].content.length === 1 && response[0].content[0].text) {
    return response[0].content[0].text
  }
  return response
}
function convertMultimodalResponseToString(response: APICallResult['response']): string | string[] {
  return Array.isArray(response) ? response.map((x) => x.content[0].text) : response.content[0].text
}

type SimpleLMPInner = (...args: any[]) => Promise<string | Array<Message>>
type SimpleLMP<A extends SimpleLMPInner> = ((...args: Parameters<A>) => Promise<string>) & {
  __ell_type__?: 'simple'
  __ell_lmp_name__?: string
  __ell_lmp_id__?: string | null
}
type ComplexLMPInner = (...args: any[]) => Promise<string | Array<Message>>
type ComplexLMP<A extends ComplexLMPInner> = ((...args: Parameters<A>) => Promise<Array<Message>>) & {
  __ell_type__?: 'complex'
  __ell_lmp_name__?: string
  __ell_lmp_id__?: string | null
}

const lmpTypeFromDefinitionType = (definitionType: LMPDefinitionType) => {
  switch (definitionType) {
    case 'simple':
      return LMPType.LM
    case 'complex':
      return LMPType.MULTIMODAL
    default:
      throw new Error(`Unknown LMP definition type: ${definitionType}`)
  }
}

/**
 * Invokes the LMP with tracking.
 * @param lmp I
 * @param args
 * @param f
 * @param a
 * @returns
 */
const invokeWithTracking = async (lmp: LMPDefinition & { lmpId: string }, args: any[], f: F, a: Kwargs) => {
  const invocationId = generateInvocationId()

  // Start the inspector session
  const session = new inspector.Session()
  session.connect()

  // Enable debugger
  const debuggerId = await session.post('Debugger.enable')

  const setBreakpoint = async (session: inspector.Session, lmp: LMPDefinition) => {
    try {
      // We use this to get the script id. The alternative is to listen to all script load events which we expect to be less performant
      // The expectation for this method is that the script has loaded and will not be reloaded, so a breakpoint at line 0 will not be hit.
     // The actual breakpoint we use to capture variables is set below
      const result = await session.post('Debugger.setBreakpointByUrl', {
        lineNumber: 0,
        url: `file://${lmp.filepath}`,
        columnNumber: 0,
      })
      logger.debug('Smoke break point', { result })
      await session.post('Debugger.removeBreakpoint', { breakpointId: result.breakpointId })
      for (const location of result.locations) {
        // Get the generated code
        const file = await resolveScriptIdToFile(session, location.scriptId)

        const source = file?.scriptSource
        if (!source) {
          throw new Error('No source found')
        }

        // Find the source map information
        const sourceMapUrl = extractSourceMapUrl(source)
        if (!sourceMapUrl) {
          throw new Error('No source map url found')
        }

        const json = getSourceMapJSON(sourceMapUrl)
        // logger.debug('sourceMap', { json })

        // Get the start and end positions of the LMP in the generated code
        const consumer = new sm.SourceMapConsumer(json)
        const generatedPositionStart = consumer.generatedPositionFor({
          source: json['sources'][0],
          line: lmp.line,
          column: 0,
        })
        const generatedPositionEnd = consumer.generatedPositionFor({
          source: json['sources'][0],
          line: lmp.endLine,
          column: 0,
        })

        // Find the best breakpoint for inspection
        //
        // We get strange behavior if a breakpoint is set to a line that isn't one of the "blessed" possible breakpoint lines
        // (the program exits with code 0 unexpectedly)
        // So we try to find the closest one
        const bestBreakpoint = await getBestClosureInspectionBreakpoint(session, location.scriptId, {
          line: generatedPositionStart.line,
          endLine: generatedPositionEnd.line,
        })
        logger.debug('bestBreakpoint', bestBreakpoint)
        const result = await session.post('Debugger.setBreakpointByUrl', {
          lineNumber: bestBreakpoint.lineNumber,
          url: `file://${lmp.filepath}`,
          columnNumber: 1,
        })
        logger.debug('LMP breakpoint set', result)
        return result.breakpointId
      }
      throw new Error('No breakpoint set')
    } catch (e) {
      logger.error('Error setting breakpoint', { err: e })
    }
  }

  let resolve: (value: void | PromiseLike<void>) => void
  let latch = new Promise((_resolve, reject) => {
    resolve = _resolve
  })

  // Listen for breakpoint hits
  session.on('Debugger.paused', async ({ params }) => {
    logger.debug('Paused on breakpoint', {
      breakpoints: params.hitBreakpoints,
      // params: JSON.stringify(params, null, 2)
    })
    const { callFrames } = params
    const scopes = callFrames[0].scopeChain

    // Get the variables you're interested in
    for (const scope of scopes) {
      if (scope.type === 'closure') {
        const result = (await session
          .post('Runtime.getProperties', {
            objectId: scope.object.objectId,
            ownProperties: false,
            accessorPropertiesOnly: false,
            generatePreview: false,
          })
          .catch((err) => {
            logger.error('Failed to get properties', err)
            return null
          })) as inspector.Runtime.GetPropertiesReturnType | null
        if (!result) {
          continue
        }
        logger.debug('closure', { result: result.result })
        for (const prop of result.result) {
          if (prop.value && prop.value.value !== undefined) {
            variableValues[prop.name] = prop.value.value
          }
        }
      }
      if (scope.type === 'local') {
        const result = (await session
          .post('Runtime.getProperties', {
            objectId: scope.object.objectId,
            ownProperties: false,
            accessorPropertiesOnly: false,
            generatePreview: false,
          })
          .catch((err) => {
            logger.error('Failed to get properties', err)
            return null
          })) as inspector.Runtime.GetPropertiesReturnType | null
        if (!result) {
          continue
        }
        logger.debug('locals', { result: JSON.stringify(result.result, null, 2) })

        for (const prop of result.result) {
          if (prop.value && prop.value.value !== undefined) {
            variableValues[prop.name] = prop.value.value
          }
        }
      }
    }

    resolve(undefined)
    // Resume execution
    // await session.post('Debugger.resume')
  })

  const breakpointId = await setBreakpoint(session, lmp)
  logger.debug('breakpointId', { breakpointId })

  let variableValues: Record<string, any> = {}

  return await invocationContext.run(
    // @ts-ignore
    {
      id: invocationId,
      lmp_id: lmp.lmpId,
    },
    async () => {
      let lmpType = lmpTypeFromDefinitionType(lmp.lmpDefinitionType)
      try {
        // for now we await this operation because it may be interrupted on exit under normal program operation
        // we should find a way to add these to a queue or something and then make sure they have all completed before the runtime exits
        await serializeLMP({
          lmp_id: lmp.lmpId,
          name: lmp.fqn,
          language: 'typescript',
          dependencies: '',
          created_at: new Date().toISOString(),
          source: lmp.source,
          lmp_type: lmpType,
          api_params: a,
          // todo. find what these refer to exactly
          initial_free_vars: {},
          initial_global_vars: {},
          // todo. requires static analysis of direct children of this lmp definition
          uses: [],
        })
      } catch (e) {
        logger.error(`Error serializing LMP: ${e}`)
      }

      const start = performance.now()
      const lmpfnoutput = await f(...args)
      // const event = await getNextPausedEvent()
      // console.log('event', event)
      // await handleBreakpointHit(event)
      // await session.post('Debugger.resume')
      await latch
      await session.post('Debugger.removeBreakpoint', { breakpointId })
      logger.debug('captured variables', { variableValues })
      // await session.post('Debugger.resume')
      await session.post('Debugger.disable')
      session.disconnect()

      const modelClient = await getModelClient(a)
      const provider = config.getProviderFor(modelClient)
      if (!provider) {
        throw new Error(`No provider found for model ${a.model} ${modelClient}`)
      }
      const messages = typeof lmpfnoutput === 'string' ? [new Message('user', lmpfnoutput)] : lmpfnoutput
      const apiParams = {
        // everything from a except tools
        ...a,
        tools: undefined,
      }
      if (config.verbose) {
        modelUsageLoggerPre({ ...lmp, name: lmp.lmpName }, args, apiParams, lmp.lmpId, messages)
      }

      const callResult = await provider.callModel(modelClient, a.model, messages, apiParams, a.tools)
      const end = performance.now()
      const latency_ms = end - start
      if (config.verbose) {
        modelUsageLoggerPostStart(lmp.lmpId, callResult.actualN)
      }

      const postIntermediate = modelUsageLoggerPostIntermediate(lmp.lmpId, callResult.actualN)

      const [trackedResults, metadata] = await provider.processResponse(callResult, 'todo', postIntermediate)
      if (config.verbose) {
        modelUsageLoggerPostEnd()
      }

      const result = convertMultimodalResponseToString(trackedResults[0])
      await serializeInvocation({
        id: invocationId,
        lmp_id: lmp.lmpId,
        latency_ms: latency_ms,
        prompt_tokens: metadata.prompt_tokens,
        completion_tokens: metadata.completion_tokens,
        contents: {
          params: args,
          results: result,
          invocation_api_params: a,
          free_vars: variableValues,
          // todo.
          global_vars: {},
          is_external: false,
        },
        used_by_id: invocationContext.getParentInvocation()?.id,
        created_at: new Date().toISOString(),

        // todo. find what these refer to
        state_cache_key: '',
        consumes: [],
      })
      return result
    }
  )
}

export const simple = <F extends SimpleLMPInner>(a: Kwargs, f: F): SimpleLMP<F> => {
  const { filepath, line, column } = getCallerFileLocation()

  if (!filepath || !line || !column) {
    logger.error(`LMP cannot be tracked. Your source maps may be incorrect or unavailable.`)
  }
  logger.debug('simple', { filepath, line, column })

  let trackAttempted = false
  // We would like to calculate the hash at runtime depending on further analysis of runtime variables
  // so i'm leaving the id part in this code instead of the static analysis tsc code for now
  let lmpId: string | undefined = undefined
  let lmpDefinition: LMPDefinition | undefined = undefined

  const wrapper: SimpleLMP<F> = async (...args: any[]) => {
    if (!wrapper.__ell_lmp_id__) {
      if (!trackAttempted) {
        trackAttempted = true
        lmpDefinition = await tsc.getLMP(filepath!, line!, column!)
        if (!lmpDefinition) {
          logger.error(
            `No LMP definition found at ${filepath}:${line}:${column}. Your source maps may be incorrect or unavailable.`
          )
        } else {
          lmpId = generateFunctionHash(lmpDefinition.source, '', lmpDefinition.lmpName)
        }
      }
    }

    if (lmpId && !a.exempt_from_tracking) {
      return await invokeWithTracking({ ...lmpDefinition!, lmpId }, args, f, a)
    }
    const lmpfnoutput = await f(...args)
    const modelClient = await getModelClient(a)
    const provider = config.getProviderFor(modelClient)
    if (!provider) {
      throw new Error(`No provider found for model ${a.model} ${modelClient}`)
    }
    const messages = typeof lmpfnoutput === 'string' ? [new Message('user', lmpfnoutput)] : lmpfnoutput
    const apiParams = {
      // everything from a except tools
      ...a,
      tools: undefined,
    }
    const callResult = await provider.callModel(modelClient, a.model, messages, apiParams, a.tools)
    const [trackedResults, metadata] = await provider.processResponse(callResult, 'todo')
    const result = convertMultimodalResponseToString(trackedResults[0])
    return result
  }

  wrapper.__ell_type__ = 'simple'
  Object.defineProperty(wrapper, '__ell_lmp_id__', {
    get: () => lmpId,
  })
  Object.defineProperty(wrapper, '__ell_lmp_name__', {
    get: () => lmpDefinition?.lmpName,
  })

  return wrapper
}

type APIParams = Record<string, any>

export const complex = <F extends SimpleLMPInner>(
  a: {
    model: string
    exempt_from_tracking?: boolean
    tools?: ToolFunction<any, any>[]
    post_callback?: (messages: Array<Message>) => void
  } & APIParams,
  f: F
): ComplexLMP<F> => {
  const { filepath, line, column } = getCallerFileLocation()

  if (!filepath || !line || !column) {
    logger.error(`LMP cannot be tracked. Your source maps may be incorrect or unavailable.`)
  }

  let trackAttempted = false
  let lmpDefinition: LMPDefinition | undefined = undefined
  let lmpId: string | undefined = undefined

  const wrapper: ComplexLMP<F> = async (...args: any[]) => {
    if (!wrapper.__ell_lmp_id__) {
      if (trackAttempted) {
        return f
      }
      trackAttempted = true
      lmpDefinition = await tsc.getLMP(filepath!, line!, column!)
      if (!lmpDefinition) {
        logger.error(`No LMP found at ${filepath}:${line}:${column}. Your source maps may be incorrect or unavailable.`)
      } else {
        lmpId = generateFunctionHash(lmpDefinition.source, '', lmpDefinition.lmpName)
      }
    }

    if (lmpId && !a.exempt_from_tracking) {
      return await invokeWithTracking({ ...lmpDefinition!, lmpId }, args, f, a)
    }
    const lmpfnoutput = await f(...args)
    const modelClient = await getModelClient(a)
    const provider = config.getProviderFor(modelClient)
    if (!provider) {
      throw new Error(`No provider found for model ${a.model} ${modelClient}`)
    }
    const messages = typeof lmpfnoutput === 'string' ? [new Message('user', lmpfnoutput)] : lmpfnoutput
    const apiParams = {
      ...a,
    }
    const callResult = await provider.callModel(modelClient, a.model, messages, apiParams, a.tools)
    const [trackedResults, metadata] = await provider.processResponse(callResult, 'todo')
    const result = trackedResults
    return result
  }

  wrapper.__ell_type__ = 'complex'
  Object.defineProperty(wrapper, '__ell_lmp_id__', {
    get: () => lmpId,
  })
  Object.defineProperty(wrapper, '__ell_lmp_name__', {
    get: () => lmpDefinition?.lmpName,
  })

  return wrapper
}

import { init } from './configurator'
import { system, user } from './types/message'
export { init, config, system, user }
