import * as z from 'zod'
import { test, expect } from 'vitest'
import path from 'path'
import { EllTSC } from '../src/util/tsc'

const pathToRepoRoot = path.resolve(__dirname, '..')

test('getLMPsInFile', async () => {
  const result = await new EllTSC().getLMPsInFile(path.resolve(path.join(__dirname, './fixtures/example.ts')))

  expect(result[0]).toEqual({
    column: 1,
    config: `{ model: 'gpt-4o' }`,
    filepath: path.join(pathToRepoRoot, '/test/fixtures/example.ts'),
    fn: `async (a: string) => {
  await child(a)
  console.log(a)
  return a
}`,
    line: 5,
    endLine: 9,
    endColumn: 3,
    lmpName: 'hello',
    fqn: 'test.fixtures.example.hello',
    lmpDefinitionType: 'simple',
    source: `const hello = simple({ model: 'gpt-4o' }, async (a: string) => {
  await child(a)
  console.log(a)
  return a
})`,
    inputSchema: undefined,
    outputSchema: undefined,
  })

  const inputSchema = result[1].inputSchema
  const outputSchema = result[1].outputSchema
  expect(outputSchema).toBeInstanceOf(z.ZodString)
  expect(inputSchema).toBeInstanceOf(z.ZodObject)
  expect(() => inputSchema?.parse({ claim_id: 42 })).toThrow(
    new z.ZodError([
      {
        code: 'invalid_type',
        expected: 'string',
        received: 'number',
        path: ['claim_id'],
        message: 'Expected string, received number',
      },
    ])
  )

  delete result[1].inputSchema
  delete result[1].outputSchema

  expect(result[1]).toEqual({
    column: 1,
    config: '',
    endColumn: 3,
    endLine: 13,
    filepath: '/Users/alexdixon/projects/ell2t/typescript/test/fixtures/example.ts',
    fqn: 'test.fixtures.example.approveClaim',
    // "inputSchema": z.object({claim_id: z.number()}),
    // "outputSchema": z.string(),
    line: 11,
    lmpDefinitionType: 'tool',
    lmpName: 'approveClaim',
    fn: 'async (input: { claim_id: string }) => {\n' + '  return `approved ${input.claim_id}`\n' + '}',
    source: `const approveClaim = ell.tool(async (input: { claim_id: string }) => {
  return \`approved \${input.claim_id}\`
})`,
  })
})
