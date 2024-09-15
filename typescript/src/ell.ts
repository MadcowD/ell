import * as sourceMapSupport from "source-map-support";
sourceMapSupport.install();

import { callsites } from "./callsites";
import { EllTSC, LMP } from "./tsc";
import { generateFunctionHash } from "./hash";

type Kwargs = { 
  // name?: string; 
  model: string; 
  [key: string]: any 
};
type F = (...args: any[]) => Promise<any>;

type StackEntry = {
  name?: string | null;
  filepath?: string | null;
  line?: number | null;
  column?: number | null;
};

let stack: StackEntry[] = [];

type Invocation = {
  lmpType: "simple" | "complex";
  args: any[];
  kwargs: Kwargs;
  input: any;
  output: any;
};
// type LMP = {
//   name: string | null;
//   filepath: string | null;
//   line: number | null;
//   column: number | null;
//   sourceCode: string | null;
// };

let tsc = new EllTSC();
export let invocations: Invocation[] = [];
export let lmps: LMP[] = [];

let lmpsCache: Record<string, LMP> = {};

const cacheKey = (filename: string, name: string) => `${filename}-${name}`;
const getLMP = async (filename: string, name: string) => {
  const key = cacheKey(filename, name);
  if (lmpsCache[key]) return lmpsCache[key];
  const lmps = await tsc.getLMPsInFile(filename);
  for (const lmp of lmps) {
    // FIXME. we need to pick the name in the config or the var name which could be different
    // const lmpName = JSON.parse(lmp.config).name
    // const k = cacheKey(filename,lmpName)
    // @ts-ignore
    // lmpsCache[k] = lmp;
  }
  const lmp = lmpsCache[key];
  // todo
  if (!lmp) {
    throw new Error(`LMP ${name} not found in file ${filename}`);
  }
  return lmp;
};

const enter = (args: StackEntry) =>
  stack.push({
    name: args.name,
    filepath: args.filepath,
    line: args.line,
    column: args.column,
  });

const exit = () => stack.pop();

const writeInvocation = async (invocation: Invocation) => {
  invocations.push(invocation);
};

const writeLMP = async (lmp: LMP) => {
  lmps.push(lmp);
};

function getCallerFileLocation() {
  const callerSite = callsites()[2];
  let file = callerSite.getFileName();
  let line = callerSite.getLineNumber();
  let column = callerSite.getColumnNumber();
  if (file && line && column) {
    const mappedPosition = sourceMapSupport.mapSourcePosition({
      source: file,
      line: line,
      column: column,
    });
    file = mappedPosition.source;
    line = mappedPosition.line;
    column = mappedPosition.column;
  }
  return { filepath: file, line, column };
}

const serializeLMP = async (args: {
  lmpId: string;
  name: string;
  filepath: string | null;
  line: number | null;
  column: number | null;
}) => {
  return await writeLMP({
    lmpId: args.lmpId,
    name: args.name,
    filepath: args.filepath,
    line: args.line,
    column: args.column,
    // sourceCode: sourceCode,
  });
};

const getLMPName = async (args: {
  filepath: string | null;
  line: number | null;
  column: number | null;
}) => {
  return "";
  // todo
  // const sourceCode = tsc.getFunctionSource(
  //   args.filepath,
  //   args.line,
  //   args.column
  // )
};

export const simple = (a: Kwargs, f: F) => {
  const { filepath, line, column } = getCallerFileLocation();

  // console.log("line", { filepath, line, column });

  if (!filepath || !line || !column) {
    console.error(
      `LMP cannot be tracked. Your source maps may be incorrect or unavailable.`
    );
    return f;
  }
  let lmp: LMP | null = null;

  const wrapper = async (...args: any[]) => {
    lmp = await tsc.getLMP(filepath!, line!, column!);
    if (!lmp) {
      console.error(
        `No LMP found at ${filepath}:${line}:${column}. Your source maps may be incorrect or unavailable.`
      );
      return f;
    }

    const lmpId = generateFunctionHash(lmp.source, "", lmp.lmpName);
    lmp.lmpId = lmpId;
    // console.log("lmp at runtime", lmp);

    const name = lmp.lmpName;
    enter({ name, filepath, line, column });
    // const lmp = await getLMP(filename,name)
    await serializeLMP({
      lmpId,
      name,
      filepath,
      line,
      column,
      ...lmp,
    });
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

  wrapper.__ell_type__ = "simple";
  Object.defineProperty(wrapper, "__ell_lmp_id__", {
    get: () => lmp?.lmpId,
  });
  Object.defineProperty(wrapper, "__ell_lmp_name__", {
    get: () => lmp?.lmpName,
  });

  return wrapper;
};

export const complex = (a: Kwargs, f: F) => {
  const name = a.name;

  const wrapper = async (...args: any[]) => {
    const { filepath, line, column } = getCallerFileLocation();
    enter({ name, filepath, line, column });
    await serializeLMP({ name, filepath, line, column });
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
