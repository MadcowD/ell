import { test, expect } from "vitest";
import { simple } from "../src/ell";
import {lmps,invocations}  from '../src/ell'

test("runtime", async () => {
  const child = simple({ model: "gpt-4o-mini" }, async (a: string) => {
    return "child";
  });
  const hello = simple({ model: "gpt-4o" }, async (a: string) => {
    const ok = await child(a);
    return a + ok;
  });

  const result = await hello("world");

  expect(result).toBe("worldchild");
  expect(hello.__ell_lmp_id__).toBeDefined();
  expect(hello.__ell_lmp_name__).toEqual('hello');
  expect(child.__ell_lmp_id__).toBeDefined();
  expect(child.__ell_lmp_name__).toEqual('child');


  // expect(lmps).toEqual([])
  expect(invocations).toEqual(
    [
      {
        "completion_tokens": expect.any(Number),
        "id": expect.stringContaining("invocation-"),
        "input": [
          "world",
        ],
        "invocation_api_params": {
          "model": "gpt-4o-mini",
        },
        "latency_ms": expect.any(Number),
        "lmp_id": expect.stringContaining("lmp-"),
        "output": "child",
        "prompt_tokens": expect.any(Number),
        "used_by_id": expect.stringContaining("invocation-")
      },
      {
        "completion_tokens": expect.any(Number),
        "id": expect.stringContaining("invocation-"),
        "input": [
          "world",
        ],
        "invocation_api_params": {
          "model": "gpt-4o",
        },
        "latency_ms": expect.any(Number),
        "lmp_id": expect.stringContaining("lmp-"),
        "output": "worldchild",
        "prompt_tokens": expect.any(Number),
        "used_by_id": undefined
      },
    ]
  )
});
