import * as ell from 'ell-ai'
import { simple, complex } from 'ell-ai'
import { child } from './example-child'

const hello = simple({ model: 'gpt-4o' }, async (a: string) => {
  await child(a)
  console.log(a)
  return a
})

const approveClaim = ell.tool(async (input: { claim_id: string }) => {
  return `approved ${input.claim_id}`
})

hello('world').then((a) => {
  console.log(a)
})
