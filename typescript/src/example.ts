import * as ell from "./ell";
import { config } from "./configurator";
import { child } from "./example-child";

config.verbose = true;
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

