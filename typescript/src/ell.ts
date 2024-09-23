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
// import * as inspectorAsync from 'inspector/promises'

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
  await session.connect()

  // Enable debugger
  const debuggerId = await session.post('Debugger.enable')


  // this only works for inline source maps. it looks like ts-node always gives those to node
  // regardless of what the tsconfig says?
  function extractSourceMapUrl(fileContent: string) {
    const sourceMapRegex = /\/\/[#@]\s*sourceMappingURL=(.+)$/m
    const match = fileContent.match(sourceMapRegex)
    if (match) {
      if (match[1].indexOf('base64,') > -1) {
        return match[1].split('base64,')[1]
      }
      return match[1]
    }
    return null
  }
  function getSourceMapJSON(base64SourceMap: string) {
    try {
      const sourceMapContent = Buffer.from(base64SourceMap, 'base64').toString()
      return JSON.parse(sourceMapContent)
    } catch (e) {
      console.error('Error parsing source map', e)
      return null
    }
  }

  async function resolveScriptIdToFile(scriptId: string) {
    try {
      const result = await session.post('Debugger.getScriptSource', { scriptId })
      console.log('scriptsource', result)
      return result
    } catch (err) {
      console.error(`Error resolving scriptId ${scriptId}:`, err)
      return err
    }
  }

  async function resolveMultipleScriptIds(scriptIds: string[]) {
    const results = []
    for (const scriptId of scriptIds) {
      try {
        const result = await resolveScriptIdToFile(scriptId)
        results.push(result)
      } catch (error) {
        console.error(`Error resolving scriptId ${scriptId}:`, error)
        results.push({ scriptId, filePath: 'Error: ' + error.message })
      }
    }
    return results
  }

  const setBreakpoint = async (lmp: LMPDefinition) => {
    try {
      const result = await session.post('Debugger.setBreakpointByUrl', {
        lineNumber: 19,
        // urlRegex: lmp.filepath.replace("\.", "\\."),
        url: 'file://' + lmp.filepath,
        columnNumber: 0,
      })
      console.log('got a breakpoint', result)
      for (const location of result.locations) {
        const file = await resolveScriptIdToFile(location.scriptId)
        const source = file.scriptSource
        const sourceMapUrl = extractSourceMapUrl(source)
        if (sourceMapUrl) {
          const json = getSourceMapJSON(sourceMapUrl)
          console.log('sourceMap', json)
          const consumer = new sm.SourceMapConsumer(json)
          const generatedPosition = consumer.generatedPositionFor({
            source: json['sources'][0],
            line: lmp.line,
            column: 0,
          })
          console.log('generatedPosition', generatedPosition)
          const result = await session.post('Debugger.setBreakpointByUrl', {
            lineNumber: generatedPosition.line + 5,
            // urlRegex: lmp.filepath.replace("\.", "\\."),
            url: 'file://' + lmp.filepath,
            columnNumber: 1,
          })
        }
      }
      return result.breakpointId
    } catch (e) {
      console.error('Error setting breakpoint', e)
    }
  }

  const breakpointId = await setBreakpoint(lmp)

  let variableValues: Record<string, any> = {}

  type BreakpointHitEvent = inspector.InspectorNotification<inspector.Debugger.PausedEventDataType>
  const getNextPausedEvent = (): Promise<BreakpointHitEvent> =>
    new Promise((resolve, reject) => {
      session.once('Debugger.paused', (params) => {
        console.log('paused', JSON.stringify(params, null, 2))
        resolve(params)
      })
    })
  const handleBreakpointHit = async ({ params }: BreakpointHitEvent) => {
    const { callFrames } = params
    const scopes = callFrames[0].scopeChain

    // Get the variables you're interested in
    for (const scope of scopes) {
      if (scope.type === 'closure') {
        const result = await session
          .post('Runtime.getProperties', {
            objectId: scope.object.objectId,
            ownProperties: false,
            accessorPropertiesOnly: false,
            generatePreview: false,
          })
          .catch((err) => {
            logger.error('Failed to get properties', err)
            return null
          })
        if (!result) {
          continue
        }
        for (const prop of result.result) {
          if (prop.value && prop.value.value !== undefined) {
            variableValues[prop.name] = prop.value.value
          }
        }
      }
    }
  }
  let resolve = undefined
  let latch = new Promise((_resolve, reject) => {
    resolve = _resolve
  })

  // Listen for breakpoint hits
  session.on('Debugger.paused', async ({ params }) => {
    console.log('paused listener', JSON.stringify(params, null, 2))
    const { callFrames } = params
    const scopes = callFrames[0].scopeChain

    // Get the variables you're interested in
    for (const scope of scopes) {
      if (scope.type === 'closure') {
        const result = await session
          .post('Runtime.getProperties', {
            objectId: scope.object.objectId,
            ownProperties: false,
            accessorPropertiesOnly: false,
            generatePreview: false,
          })
          .catch((err) => {
            logger.error('Failed to get properties', err)
            return null
          })
        if (!result) {
          continue
        }
        for (const prop of result.result) {
          if (prop.value && prop.value.value !== undefined) {
            variableValues[prop.name] = prop.value.value
          }
        }
      }
      if (scope.type === 'local') {
        const result = await session
          .post('Runtime.getProperties', {
            objectId: scope.object.objectId,
            ownProperties: false,
            accessorPropertiesOnly: false,
            generatePreview: false,
          })
          .catch((err) => {
            logger.error('Failed to get properties', err)
            return null
          })
        if (!result) {
          continue
        }

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

  return await invocationContext.run(
    // @ts-ignore
    {
      id: invocationId,
      lmp_id: lmp.lmpId,
    },
    async () => {
      let lmpType = lmpTypeFromDefinitionType(lmp.lmpDefinitionType)
      try {
        // fire and forget
        serializeLMP({
          lmp_id: lmp.lmpId,
          name: lmp.lmpName,
          dependencies: '',
          created_at: new Date().toISOString(),
          source: lmp.source,
          lmp_type: lmpType,
          api_params: a,
          // todo. requires runtime inspection of the user-provided closure
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
      console.log('Capturedvariables', variableValues)
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
      serializeInvocation({
        id: invocationId,
        lmp_id: lmp.lmpId,
        latency_ms: latency_ms,
        prompt_tokens: metadata.prompt_tokens,
        completion_tokens: metadata.completion_tokens,
        contents: {
          params: args,
          results: result,
          invocation_api_params: a,
          // todo.
          global_vars: {},
          free_vars: {},
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
import { ToolFunction } from './types/tools'
import { WriteInvocationInput, WriteLMPInput } from './serialize/sql'
import { LMPType } from './lmp/types'
export { init, config, system, user }
