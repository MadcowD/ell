import { LMPType } from "../lmp/types"



// API types
export type ISODateString = string

export type WriteLMPInput = {
    lmp_id: string
    name: string
    source: string
    language: 'python' | 'typescript'
    dependencies: string
    created_at: ISODateString
    lmp_type: LMPType
    api_params: Record<string, any>
    initial_free_vars: Record<string, any>
    initial_global_vars: Record<string, any>
    commit_message: string
    version_number: number
    uses: string[]
  }
  
  export type WriteInvocationContentsInput = {
    params: Record<string, any>
    results: any
    invocation_api_params: Record<string, any>
    global_vars: Record<string, any>
    free_vars: Record<string, any>
    is_external?: boolean
  }
  
  export type WriteInvocationInput = {
    id: string
    lmp_id: string
    latency_ms: number
    prompt_tokens: number
    completion_tokens: number
    state_cache_key: string
    created_at: ISODateString
    used_by_id: string | undefined
    contents: WriteInvocationContentsInput
    consumes: string[]
  }