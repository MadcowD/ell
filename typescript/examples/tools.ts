import * as ell from 'ell-ai'

ell.init()

const getWeather = ell.tool(
  async ({ location }: { location: string }) => {
    // Simulated weather API call
    return `The weather in ${location} is sunny.`
  },
  {
    description: 'Get the current weather for a given location.',
    paramDescriptions: { location: 'The full name of a city and country, e.g. San Francisco, CA, USA' },
  }
)

const travelPlanner = ell.complex({ model: 'gpt-4o', tools: [getWeather] }, async (destination: string) => {
  return [
    ell.system('You are a travel planner. Use the weather tool to provide relevant advice.'),
    ell.user(`Plan a trip to ${destination}`),
  ]
})

;(async () => {
  const result = await travelPlanner('Paris')
  console.log(result.text) // Prints travel advice
  if (result.toolCalls) {
    // This is done so that we can pass the tool calls to the language model
    const tool_results = await result.callToolsAndCollectAsMessage()
    console.log('Weather info:', tool_results.text)
  }
})()
