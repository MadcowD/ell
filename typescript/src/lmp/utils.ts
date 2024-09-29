import * as sourceMapSupport from 'source-map-support'
import { Kwargs } from "./types"
import { config } from "../configurator"
import { APICallResult } from "../provider"
import { Message } from "../types/message"
import { callsites } from '../util/callsites'

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
export function convertMultimodalResponseToString(response: APICallResult['response']): string | string[] {
  return Array.isArray(response) ? response.map((x) => x.content[0].text) : response.content[0].text
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