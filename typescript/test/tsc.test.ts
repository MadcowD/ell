import { test, expect } from 'vitest'
import path from 'path'
import { EllTSC } from '../src/tsc'

const pathToRepoRoot = path.resolve(__dirname, '..')

test('getLMPsInFile', async () => {
  const result = await new EllTSC().getLMPsInFile(path.resolve(path.join(__dirname, './fixtures/example.ts')))

  expect(result).toEqual([
    {
      column: 1,
      config: `{ model: 'gpt-4o' }`,
      filepath: path.join(pathToRepoRoot, '/test/fixtures/example.ts'),
      fn: `async (a: string) => {
  await child(a)
  console.log(a)
}`,
      line: 5,
      endLine: 8,
      endColumn: 3,
      lmpName: 'hello',
      lmpDefinitionType: 'simple',
      source: `const hello = simple({ model: 'gpt-4o' }, async (a: string) => {
  await child(a)
  console.log(a)
})`,
    },
  ])
})
