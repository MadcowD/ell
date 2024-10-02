import * as crypto from 'crypto'

export function generateFunctionHash(source: string, dsrc: string, qualname: string): string {
  const combinedString = [source, dsrc, qualname].join('\n')
  const hash = crypto.createHash('md5').update(combinedString).digest('hex')
  return `lmp-${hash}`
}

export function generateInvocationId(): string {
  return `invocation-${crypto.randomBytes(16).toString('hex')}`
}