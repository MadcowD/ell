type Kwargs = Record<'name'|'model', string>
type F = (...args: any[]) => Promise<any>
export const lm = (a: any, f: F) => {
  return f
}
export const simple = (a: any, f: F) => {
  return f
}
export const complex= (a: any, f: F) => {
  return f
}
