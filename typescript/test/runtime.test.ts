import { test, expect, beforeAll } from "vitest";
import { simple } from "../src/ell";
import {lmps,invocations}  from '../src/ell'
import { config } from "../src/configurator";
import OpenAI from "openai";

beforeAll(() => {
  // @ts-expect-error
  config.defaultClient.chat.completions.create = async (...args) => {
    console.log('chat.completions.create called with', args)
    return <OpenAI.Chat.Completions.ChatCompletion>{
      usage: {
        prompt_tokens: 10,
        completion_tokens: 10,
        latency_ms: 10,
        total_tokens: 20,
      },
      id: 'chatcmpl-123',
      created: 1677652288,
      model: 'gpt-3.5-turbo-0125',
      object: 'chat.completion',
      choices: [
        <OpenAI.Chat.Completions.ChatCompletion.Choice>{
          index: 0,
          finish_reason: 'stop',
          logprobs: null,
          message: {
            // @ts-expect-error
            content: args[0].messages[0].content[0].text,
            role: 'assistant',
            refusal: null,
          },
        },
      ],
    }
  }
})
test("runtime", async () => {
  const child = simple({ model: "gpt-4o-mini" }, async (a: string) => {
    return "child"
  });
  const hello = simple({ model: "gpt-4o" }, async (a: {a: string}) => {
    const ok = await child(a.a);
    return a.a + ok;
  });

  const result = await hello({a: "world"});

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
        "invocation_contents": {
          "invocation_api_params": {
            "model": "gpt-4o-mini",
          },
          "invocation_id": expect.stringContaining("invocation-"),
          "params": [
             "world",
          ],
          "results": "child",
        },
        "latency_ms": expect.any(Number),
        "lmp_id": expect.stringContaining("lmp-"),
        "prompt_tokens": expect.any(Number),
        "used_by_id": expect.stringContaining("invocation-")
      },
      {
        "completion_tokens": expect.any(Number),
        "id": expect.stringContaining("invocation-"),
        "invocation_contents": {
          "invocation_api_params": {
            "model": "gpt-4o",
          },
          "invocation_id": expect.stringContaining("invocation-"),
          "params": [
            {a:'world'}
          ],
          "results": "worldchild",
        },
        "latency_ms": expect.any(Number),
        "lmp_id": expect.stringContaining("lmp-"),
        "prompt_tokens": expect.any(Number),
        "used_by_id": undefined
      },
    ]
  )
});
