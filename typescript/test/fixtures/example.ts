import * as ell from '../../src'
import { simple, complex } from '../../src'
import { child } from './example-child'

const hello = simple({ model: 'gpt-4o' }, async (a: string) => {
  await child(a)
  console.log(a)
  return a
})

hello('world').then((a) => {
  console.log(a)
})
