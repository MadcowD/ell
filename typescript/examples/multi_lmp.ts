import * as ell from '../src/ell'

const generateStoryIdeas = ell.simple({ model: 'gpt-4o-mini', temperature: 1.0 }, async (about: string) => {
  return [
    ell.system('You are an expert story ideator. Only answer in a single sentence.'),
    ell.user(`Generate a story idea about ${about}.`),
  ]
})

const writeADraftOfAStory = ell.simple({ model: 'gpt-4o-mini', temperature: 1.0 }, async (idea: string) => {
  return [
    ell.system('You are an adept story writer. The story should only be 3 paragraphs.'),
    ell.user(`Write a story about ${idea}.`),
  ]
})

const chooseTheBestDraft = ell.simple({ model: 'gpt-4o', temperature: 0.1 }, async (drafts: string[]) => {
  return [
    ell.system('You are an expert fiction editor.'),
    ell.user(`Choose the best draft from the following list: ${drafts.join('\n')}`),
  ]
})

const writeAReallyGoodStory = ell.simple({ model: 'gpt-4-turbo', temperature: 0.2 }, async (about: string) => {
  // 4 ideas
  let ideas = []
  for (let i = 0; i < 4; i++) {
    ideas.push(await generateStoryIdeas(about))
  }
  const drafts = await Promise.all(ideas.map(writeADraftOfAStory))
  const bestDraft = await chooseTheBestDraft(drafts)

  return [
    ell.system('You are an expert novelist that writes in the style of Hemingway. You write in lowercase.'),
    ell.user(`Make a final revision of this story in your voice: ${bestDraft}`),
  ]
})

;(async () => {
  ell.init({ store: './logdir', autocommit: true, verbose: true })

  const story = await writeAReallyGoodStory('a dog')
  console.log(story)
})()
