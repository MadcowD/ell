import { simple,complex } from "./ell";

const hello = simple({ name: "hello", model: "gpt-4o" }, async (a: string) => {
  console.log(a);
});

hello("world").then((a) => {
  console.log(a);
});
