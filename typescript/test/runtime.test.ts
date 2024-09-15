import { test, expect } from "vitest";
import { simple } from "../src/ell";

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
});
