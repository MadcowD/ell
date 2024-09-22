import * as ell from '../src/ell' // Assuming there's a TypeScript-compatible 'ell' library

ell.init({
  store: './logdir',
  autocommit: true,
  verbose: true,
})

const randomChoice = (arr: string[]) => {
  return arr[Math.floor(Math.random() * arr.length)]
}

function getRandomAdjective(): string {
  const adjectives = ['enthusiastic', 'cheerful', 'warm', 'friendly', 'heartfelt', 'sincere']
  return randomChoice(adjectives)
}

function getRandomPunctuation(): string {
  return randomChoice(['!', '!!', '!!!'])
}

const hello = ell.simple({ model: 'gpt-4o-mini' }, async (name: string) => {
  const adjective = getRandomAdjective()
  const punctuation = getRandomPunctuation()
  return [
    ell.system('You are a helpful and expressive assistant.'),
    ell.user(`Say a ${adjective} hello to ${name}${punctuation}`),
  ]
})

;(async () => {
  const greeting = await hello('Sam Altman')
  console.log(greeting)
})()
