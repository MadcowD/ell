import { z } from 'zod'

type AnyZodSchema = z.ZodType<any>

type ToolArgs<Name, Input, Output> = {
  name: Name
  input: Input
  output: Output
  description: string
}
export type ToolFunction<Input, Output> = (args: Input) => Promise<Output>
export type Tool<Input, Output> = ToolFunction<Input, Output> & {
  __ell_tool_input: z.ZodType<Input>
  __ell_tool_output: z.ZodType<Output>
  __ell_tool_name: string
  __ell_tool_description: string
  __is_tool: true
}

export const tool = <
  const Name extends string,
  Input extends AnyZodSchema,
  Output extends AnyZodSchema,
  Args extends ToolArgs<Name, Input, Output>,
>(
  args: Args,
  f: ToolFunction<z.infer<Input>, z.infer<Output>>
) => {
  Object.assign(f, {
    __ell_tool_input__: args.input,
    __ell_tool_output__: args.output,
    __ell_tool_name__: args.name,
    __ell_tool_description__: args.description,
    __ell_is_tool__: true,
  })
  return f
}

export const toolFromZodFunction = <Args extends z.ZodTuple, Output extends z.ZodObject<any>>(
  zf: z.ZodFunction<Args, Output>,
  f: (...args: z.infer<Args>) => Promise<z.infer<Output>>
) => {
  Object.assign(f, {
    __ell_tool_input__: zf._input,
    __ell_tool_output__: zf._output,
    __ell_tool_name__: 'todo',
    __ell_tool_description__: zf._def.description,
    __ell_is_tool__: true,
  })
  return f
}

const mytool2 = toolFromZodFunction(
  z
    .function(
      z.tuple([z.object({ hello: z.string() })]).describe('This is a test tool input'),
      z.object({ world: z.string() }).describe('This is a test tool output')
    )
    .describe('This is a test tool'),

  async (args) => {
    return { world: 'world' }
  }
)

const mytool = tool(
  {
    name: 'mytool',
    input: z.object({ hello: z.string() }).describe('This is a test tool'),
    output: z.object({ world: z.string() }).describe('This is a test tool'),
    description: 'This is a test tool',
  },
  async (args) => {
    return { world: 'world' }
  }
)
