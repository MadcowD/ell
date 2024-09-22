import * as ell from './ell'
import { simple, complex } from './ell'
import { child } from './example-child'

const hello = simple({ model: 'gpt-4o' }, async (a: string) => {
  await child(a)
  console.log(a)
})

hello('world').then((a) => {
  console.log(a)
  console.log(ell.invocations)
  console.log(ell.lmps)
})
