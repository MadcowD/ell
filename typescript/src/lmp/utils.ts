import * as sourceMapSupport from 'source-map-support'
import { Kwargs } from './types'
import { config } from '../configurator'
import { Message } from '../types/message'
import { callsites } from '../util/callsites'
import * as logging from '../util/_logging'

const logger = logging.getLogger('ell')

export const getModelClient = async (args: Kwargs) => {
  if (args.client) {
    return args.client
  }
  const [client, _fallback] = config.getClientFor(args.model)
  return client
}

export const convertMultimodalResponseToLstr = (response: Message[]) => {
  if (response.length === 1 && response[0].content.length === 1 && response[0].content[0].text) {
    return response[0].content[0].text
  }
  return response
}

export function convertMultimodalResponseToString(response: Message | Message[]): string | string[] {
  if (Array.isArray(response)) {
    return response.map((x) => {
      const text = x.content[0].text
      if (text) {
        return text
      }
      logger.warn(`No text found in message: ${JSON.stringify(x)}`)
      return ''
    })
  }
  const text = response.content[0].text
  if (text) {
    return text
  }
  logger.warn(`No text found in message: ${JSON.stringify(response)}`)
  return ''
}

export function getCallerFileLocation() {
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
