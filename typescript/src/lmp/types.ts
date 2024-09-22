export const LMPType = {
  LM: 'LM',
  TOOL: 'TOOL',
  MULTIMODAL: 'MULTIMODAL',
  OTHER: 'OTHER',
}

export type LMPType = typeof LMPType[keyof typeof LMPType]
