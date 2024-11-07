import { Message } from '../types/message'
import { invokeWithTracking } from './_track'
import { convertMultimodalResponseToString, getCallerFileLocation, getModelClient } from './utils'
import { config } from '../configurator'
import * as logging from '../util/_logging'
import { Kwargs } from './types'
import { LMPDefinition, tsc } from '../util/tsc'
import { generateFunctionHash } from '../util/hash'
import { EllCallParams } from '../provider'

const logger = logging.getLogger('ell')

type SimpleLMPInner = (...args: any[]) => string | Array<Message> | Promise<string | Array<Message>>
type SimpleLMP<A extends SimpleLMPInner> = ((...args: Parameters<A>) => Promise<string>) & {
  __ell_type__?: 'simple'
  __ell_lmp_name__?: string
  __ell_lmp_id__?: string | null
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
    const promptFnOutput = await Promise.resolve(f(...args))
    const modelClient = await getModelClient(a)
    const provider = config.getProviderFor(modelClient)
    if (!provider) {
      throw new Error(`No provider found for model ${a.model} ${modelClient}`)
    }
    const messages = typeof promptFnOutput === 'string' ? [new Message('user', promptFnOutput)] : promptFnOutput
    const apiParams = {
      // simple case: everything from `a` except tools
      ...a,
      tools: undefined,
    }
    const ellCall: EllCallParams = {
      model: a.model,
      messages: messages,
      client: modelClient,
      tools: a.tools,
      apiParams: apiParams,
    }
    const [providerResult, _finalApiParams, _metadata] = await provider.call(ellCall)
    const result = convertMultimodalResponseToString(providerResult[0])
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
