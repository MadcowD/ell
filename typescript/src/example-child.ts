import * as ell from "./ell";

export const child = ell.simple({name: "child", model: "gpt-4o"}, async (a: string) => {
  console.log('child', a);
});
