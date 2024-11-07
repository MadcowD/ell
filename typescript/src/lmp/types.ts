import { ZodType } from "zod"

export const LMPType = {
  LM: 'LM',
  TOOL: 'TOOL',
  MULTIMODAL: 'MULTIMODAL',
  OTHER: 'OTHER',
}

export type LMPType = typeof LMPType[keyof typeof LMPType]


export type Kwargs = {
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

export type APIParams = Record<string, any>


// todo. json schema
export type ResponseFormatSchema = ZodType<any, any, any>

export type ResponseFormatValue<ResponseFormat extends ResponseFormatSchema> =
  ResponseFormat extends ZodType<infer T> ? T : never
