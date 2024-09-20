import * as ell from "./ell";
import { child } from "./example-child";

export const hello = ell.simple({ model: "gpt-4o" }, 
  async (a: string) => {
    return await child(a);
});

// ell.init()
hello("world").then((result) => {
  console.log(result);
  console.log(ell.invocations);
  console.log(ell.lmps);
});

