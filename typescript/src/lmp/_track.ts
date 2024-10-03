import { performance } from 'perf_hooks'
import * as inspector from 'inspector/promises'
import { AsyncLocalStorage } from 'async_hooks'
import * as sm from 'source-map'
import {
  extractSourceMapUrl,
  getBestClosureInspectionBreakpoint,
  getSourceMapJSON,
  resolveScriptIdToFile,
} from './../util/closure'
import { generateInvocationId } from '../util/hash'
import { LMPDefinition, LMPDefinitionType } from '../util/tsc'
import { Kwargs, LMPType } from './types'
import { Message } from '../types/message'
import { Logger } from '../util/_logging'
import {
  modelUsageLoggerPostEnd,
  modelUsageLoggerPostIntermediate,
  modelUsageLoggerPostStart,
  modelUsageLoggerPre,
} from './../util/verbosity'
import { config } from '../configurator'
import { convertMultimodalResponseToString, getModelClient } from './utils'
import { serializeInvocation, serializeLMP } from '../serialize'

const logger = new Logger('track')

export type InvocationContents = {
  invocation_id: any
  params: any
  results: any
  invocation_api_params: any
}

export type Invocation = {
  id: string
  lmp_id: string
  latency_ms: number
  prompt_tokens: number
  completion_tokens: number
  invocation_contents: InvocationContents
  used_by_id?: string
}




type F = (...args: any[]) => Promise<string | Array<Message>>

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
const invocationContext = new InvocationContext()

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
 * @param lmp
 * @param args
 * @param f
 * @param a
 * @returns
 */
export const invokeWithTracking = async (lmp: LMPDefinition & { lmpId: string }, args: any[], f: F, a: Kwargs) => {
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
        // So we try to find the closest one to the ending return statement of the LMP
        let bestBreakpoint = await getBestClosureInspectionBreakpoint(session, location.scriptId, {
          line: generatedPositionStart.line,
          endLine: generatedPositionEnd.line,
        })
        if (!bestBreakpoint) {
          logger.debug('No best breakpoint found, using start line')
          bestBreakpoint = {
            scriptId: location.scriptId,
            lineNumber: generatedPositionStart.line,
            columnNumber: generatedPositionStart.column,
          }
        } else {
          logger.debug('bestBreakpoint', bestBreakpoint)
        }
        const result = await session.post('Debugger.setBreakpointByUrl', {
          url: `file://${lmp.filepath}`,
          lineNumber: bestBreakpoint.lineNumber,
          columnNumber: bestBreakpoint.columnNumber,
        })
        logger.debug('LMP breakpoint set', result)
        return result.breakpointId
      }
      logger.debug('No breakpoint could be set')
      return null
    } catch (e) {
      logger.error('Error setting breakpoint', { err: e })
    }
  }

  let resolve: (value: void | PromiseLike<void>) => void
  let latch = new Promise((_resolve, reject) => {
    resolve = _resolve
  })

  const handleBreakpointHit = async ({ params }: { params: inspector.Debugger.PausedEventDataType }) => {
    // TODO. For performance we should aggressively filter the breakpoints we set.
    // This function runs whenever the debugger pauses, including a user's "step-into/step-over" etc.
    // When using "step into/out/over", hitBreakpoints is empty
    if (!params.hitBreakpoints || params.hitBreakpoints.length === 0) {
      return
    }
    logger.debug('Paused on breakpoint', {
      breakpoints: params.hitBreakpoints,
      // params: JSON.stringify(params, null, 2)
    })
    const { callFrames } = params
    const scopes = callFrames[0].scopeChain

    // Get the variables we're interested in
    //
    // TODO. Once we have clarified what is needed for free vars vs global vars
    // we should be able to get everything we need here, potentially from scope.type === 'global' in addition to these
    // There is additional line information on the scope that is available for us to use
    // for checking we're in the right spot. 
    // For now we expect to do this work when we set breakpoints in the first place
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

    // By this time we assume we captured all variables of interest
    session.off('Debugger.paused', handleBreakpointHit)
    
    resolve(undefined)
  }

  // Listen for breakpoint hits
  session.on('Debugger.paused', handleBreakpointHit)

  const breakpointId = await setBreakpoint(session, lmp)

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
          // todo. requires static analysis of direct children of this lmp definition?
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

      const result =
        lmp.lmpDefinitionType === 'simple' ? convertMultimodalResponseToString(trackedResults[0]) : trackedResults
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
      return result.length === 1 ? result[0] : result
    }
  )
}
