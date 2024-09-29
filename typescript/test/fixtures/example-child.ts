import * as ell from 'ell-ai'

export const child = ell.simple({ model: 'gpt-4o' }, async (a: string) => {
  console.log('child', a)
  throw new Error('test')
})
