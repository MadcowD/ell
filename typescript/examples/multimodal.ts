import * as ell from 'ell-ai'

const describeImage = ell.complex({ model: 'gpt-4o-mini' }, (url: string) => [
  ell.system('You are a helpful assistant that can help people see.'),
  ell.user('Please describe this image in glorious detail.'),
  ell.user(new ell.ImageContent({ url, detail: 'low' })),
])

;(async () => {
  ell.init({ verbose: true })
  const imageURL = 'https://www.pbs.org/wnet/nature/files/2014/09/ExtraordinaryCats-Main-900x506.jpg'
  const result = await describeImage(imageURL)
  console.log(result.text)
})()
