import * as sourceMapSupport from "source-map-support";
sourceMapSupport.install();

import { AsyncLocalStorage } from "async_hooks";
import { callsites } from "./callsites";
import { EllTSC, LMP } from "./tsc";
import { generateFunctionHash, generateInvocationId } from "./hash";

type Kwargs = {
  // The name or identifier of the language model to use.
  model: string;
  // An optional OpenAI client instance.
  client?: any; //OpenAI
  // A list of tool functions that can be used by the LLM.
  tools?: any[];
  // If True, the LMP usage won't be tracked.
  exempt_from_tracking?: boolean;
  // Additional API parameters
  [key: string]: any;
};

type F = (...args: any[]) => Promise<any>;

type InvocationContents = {
  invocation_id: any;
  params: any;
  results: any;
  invocation_api_params: any;
};

type Invocation = {
  id: string;
  lmp_id: string;
  latency_ms: number;
  prompt_tokens: number;
  completion_tokens: number;
  invocation_contents: InvocationContents;
  used_by_id?: string;
};

let tsc = new EllTSC();

// todo. storage
export let invocations: Invocation[] = [];
export let lmps: LMP[] = [];

class InvocationContext {
  private storage: AsyncLocalStorage<Invocation[]>;

  constructor() {
    this.storage = new AsyncLocalStorage<Invocation[]>();
  }

  async run(invocation: Invocation, callback: () => Promise<void>) {
    let stack = this.storage.getStore() || [];
    stack = [...stack, invocation];
    return this.storage.run(stack, callback);
  }

  getCurrentInvocation(): Invocation | undefined {
    const stack = this.storage.getStore();
    return stack ? stack[stack.length - 1] : undefined;
  }
  getParentInvocation(): Invocation | undefined {
    const stack = this.storage.getStore();
    return stack && stack.length > 1 ? stack[stack.length - 2] : undefined;
  }
}

const invocationContext = new InvocationContext();
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

const serializeLMP = async (args: LMP) => {
  // todo. commit message if not exists
  return await writeLMP(args);
};

type Wrapper = {
  (...args: any[]): Promise<any>;
  __ell_type__?: string;
  __ell_lmp_name__?: string;
  __ell_lmp_id__?: string | null;
  __ell_invocation_id__?: string | null;
};

export const simple = (a: Kwargs, f: F):Wrapper => {
  const { filepath, line, column } = getCallerFileLocation();

  if (!filepath || !line || !column) {
    console.error(
      `LMP cannot be tracked. Your source maps may be incorrect or unavailable.`
    );
    return f;
  }

  let maybeLMP: LMP | null = null;
  let trackAttempted = false;
  let lmp: LMP = undefined as unknown as LMP;

  const wrapper: Wrapper = async (...args: any[]) => {
    if (!wrapper.__ell_lmp_id__) {
      if (trackAttempted) {
        return f;
      }
      trackAttempted = true;
      maybeLMP = await tsc.getLMP(filepath!, line!, column!);
      if (!maybeLMP) {
        console.error(
          `No LMP found at ${filepath}:${line}:${column}. Your source maps may be incorrect or unavailable.`
        );
        return f;
      }
      lmp = maybeLMP;
      const lmpId = generateFunctionHash(maybeLMP.source, "", maybeLMP.lmpName);
      lmp.lmpId = lmpId;
      lmp.apiParams = a;
    }
    let invocationId = generateInvocationId();
    return invocationContext.run(
      {
        id: invocationId,
        lmp_id: lmp.lmpId,
      },
      async () => {
        // const lmp = await getLMP(filename,name)
        await serializeLMP(lmp);
        const lmpfnoutput = await f(...args);
        const invokeModel = async (input: any) => {
          return input;
        };

        const modelResult = await invokeModel(lmpfnoutput);
        const result = modelResult;
        await writeInvocation({
          id: invocationId,
          lmp_id: lmp.lmpId,
          latency_ms: 0,
          prompt_tokens: 0,
          completion_tokens: 0,
          input: args,
          output: modelResult,
          invocation_api_params: a,
          used_by_id: invocationContext.getParentInvocation()?.id,
        });
        return result;
      }
    );
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
