import { callsites } from "./callsites";

type Kwargs = Record<"name" | "model", string>;
type F = (...args: any[]) => Promise<any>;

type StackEntry = {
  name: string;
  filename: string;
};

let stack: StackEntry[] = [];

type Invocation = {
  lmpType: "simple" | "complex";
  args: any[];
  kwargs: Kwargs;
  input: any;
  output: any;
};
type LMP = {
  name: string;
  filename: string;
  sourceCode: string;
};

export let invocations: Invocation[] = [];
export let lmps: LMP[] = [];

const enter = (args: StackEntry) =>
  stack.push({ name: args.name, filename: args.filename });

const exit = () => stack.pop();

const writeInvocation = async (invocation: Invocation) => {
  invocations.push(invocation);
};

const writeLMP = async (lmp: LMP) => {
  lmps.push(lmp);
};

function getCallerFile() {
  const callerFile = callsites()[2].getFileName();
  return callerFile ? callerFile : "unknown";
}
const serializeLMP = async (args: { name: string; filename: string }) => {
  const sourceCode = "";
  return await writeLMP({
    name: args.name,
    filename: args.filename,
    sourceCode: sourceCode,
  });
};

export const simple = (a: Kwargs, f: F) => {
  const name = a.name;
  const filename = getCallerFile();

  const wrapper = async (...args: any[]) => {
    enter({ name, filename });
    await serializeLMP({ name, filename });
    const result = await f(...args);
    await writeInvocation({
      lmpType: "simple",
      args,
      kwargs: a,
      input: args,
      output: result,
    });
    exit();
    return result;
  };
  return wrapper;
};

export const complex = (a: Kwargs, f: F) => {
  const name = a.name;

  const wrapper = async (...args: any[]) => {
    const filename = __filename;
    enter({ name, filename });
    await serializeLMP({ name, filename });
    const result = await f(...args);
    await writeInvocation({
      lmpType: "complex",
      args,
      kwargs: a,
      input: args,
      output: result,
    });
    exit();
    return result;
  };
  return wrapper;
};

const track = () => {};
