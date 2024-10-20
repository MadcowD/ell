import { generateFunctionHash } from '../util/hash'
import { Message } from '../types/message'
import { invokeWithTracking } from './_track'
import { config } from '../configurator'
import { getCallerFileLocation, getModelClient } from './utils'
import { APIParams, ResponseFormatSchema } from './types'
import { ToolFunction } from '../types/tools'
import { LMPDefinition, tsc } from '../util/tsc'
import * as logging from '../util/_logging'
import { EllCallParams } from '../provider'

const logger = logging.getLogger('ell')

type ComplexLMPInner = (...args: any[]) => Promise<Array<Message>>
type ComplexLMP<A extends ComplexLMPInner, ResponseFormat extends ResponseFormatSchema> = ((
  ...args: Parameters<A>
) => Promise<ResponseFormat extends any ? Message<ResponseFormat> : Array<Message>>) & {
  __ell_type__?: 'complex'
  __ell_lmp_name__?: string
  __ell_lmp_id__?: string | null
}

/***
    A sophisticated language model programming decorator for complex LLM interactions.

    This decorator transforms a function into a Language Model Program (LMP) capable of handling
    multi-turn conversations, tool usage, and various output formats. It's designed for advanced
    use cases where full control over the LLM's capabilities is needed.

    @param {string} model - The name or identifier of the language model to use.
    @param {any} [client] - An optional OpenAI client instance. If not provided, a default client will be used.
    @param {Callable[]} [tools] - A list of tool functions that can be used by the LLM. Only available for certain models.
    @param {Record<string, any>} [response_format] - The response format for the LLM. Only available for certain models.
    @param {number} [n] - The number of responses to generate for the LLM. Only available for certain models.
    @param {number} [temperature] - The temperature parameter for controlling the randomness of the LLM.
    @param {number} [max_tokens] - The maximum number of tokens to generate for the LLM.
    @param {number} [top_p] - The top-p sampling parameter for controlling the diversity of the LLM.
    @param {number} [frequency_penalty] - The frequency penalty parameter for controlling the LLM's repetition.
    @param {number} [presence_penalty] - The presence penalty parameter for controlling the LLM's relevance.
    @param {string[]} [stop] - The stop sequence for the LLM.
    @param {boolean} [exempt_from_tracking=false] - If true, the LMP usage won't be tracked.
    @param {Callable} [post_callback] - An optional function to process the LLM's output before returning.
    @param {Record<string, any>} [api_params] - Additional keyword arguments to pass to the underlying API call.
    @returns {Function} A decorator that can be applied to a function, transforming it into a complex LMP.
    

    Functionality:

    1. Advanced LMP Creation:
       - Supports multi-turn conversations and stateful interactions.
       - Enables tool usage within the LLM context.
       - Allows for various output formats, including structured data and function calls.

    2. Flexible Input Handling:
       - Can process both single prompts and conversation histories.
       - Supports multimodal inputs (text, images, etc.) in the prompt.

    3. Comprehensive Integration:
       - Integrates with ell's tracking system for monitoring LMP versions, usage, and performance.
       - Supports various language models and API configurations.

    4. Output Processing:
       - Can return raw LLM outputs or process them through a post-callback function.
       - Supports returning multiple message types (e.g., text, function calls, tool results).

    Usage Modes and Examples:

    1. Basic Prompt:

    ```typescript
    const generateStory = ell.complex({ model: "gpt-4" }, 
        async (prompt: string): Promise<ell.Message[]> => {
            // System prompt
            return [
                ell.system("You are a creative story writer"),
                ell.user(`Write a short story based on this prompt: ${prompt}`)
            ];
        }
    );

    (async () => {
        const story = await generateStory("A robot discovers emotions");
        console.log(story[0].content);  // Access the content of the first (and only) message
    })();
    ```

    2. Multi-turn Conversation:

    ```typescript
    const chatBot = complex({ 
        model: "gpt-4",
        exempt_from_tracking: false,
        api_params: {}
    }, 
    async (messageHistory: ell.Message[]): Promise<ell.Message[]> => {
        return [
            ell.system("You are a helpful assistant."),
            ...messageHistory
        ];
    });

    (async () => {
        const conversation: ell.Message[] = [
            ell.user("Hello, who are you?"),
            ell.assistant("I'm an AI assistant. How can I help you today?"),
            ell.user("Can you explain quantum computing?")
        ];

        const response: ell.Message[] = await chatBot(conversation);
        console.log(response[response.length - 1].content);  // Print the assistant's response
    })();
    ```

    3. Tool Usage:

    ```typescript
    // Define the structure for weather data
    interface WeatherData {
      temperature: number;
      condition: string;
    }

    // Weather tool function
    const getWeather = ell.tool<[string], WeatherData>()(
        async (location: string): Promise<WeatherData> => {
        // Simulate a weather API call
        await new Promise(resolve => setTimeout(resolve, 1000));
        return {
            temperature: Math.round(Math.random() * 30 + 10), // Random temp between 10-40°C
            condition: ['Sunny', 'Cloudy', 'Rainy', 'Windy'][Math.floor(Math.random() * 4)]
        };
    };

    // Weather assistant function
    const weatherAssistant = ell.complex({
        model: "gpt-4",
        tools: [getWeather],
        exempt_from_tracking: false,
    })(
    async (messageHistory: ell.Message[]): Promise<ell.Message[]> => {
        return [
        ell.system("You are a weather assistant. Use the getWeather tool when needed."),
        ...messageHistory
        ];
    }
    );

    // Usage example
    (async () => {
    const conversation: ell.Message[] = [
        ell.user("What's the weather like in New York?")
    ];

    const response = await weatherAssistant(conversation);
    const lastMessage = response[response.length - 1];

    if (lastMessage.tool_calls && lastMessage.tool_calls.length > 0) {
        const toolResults = await lastMessage.call_tools_and_collect_as_message();
        console.log("Tool results:", toolResults.content);

        // Continue the conversation with tool results
        const finalResponse = await weatherAssistant([...conversation, lastMessage, toolResults]);
        console.log("Final response:", finalResponse[finalResponse.length - 1].content);
    } else {
        console.log("Response:", lastMessage.content);
    }
    })();
    ```

    4. Structured Output:

    ```typescript
    import { z } from 'zod';
    import { Message } from './types';

    const PersonInfo = z.object({
    name: z.string(),
    age: z.number()
    });

    type PersonInfo = z.infer<typeof PersonInfo>;

    const extractPersonInfo = ell.complex({
    model: "gpt-4",
    response_format: PersonInfo
    })(
    async (text: string): Promise<Message[]> => {
        return [
        ell.system("Extract person information from the given text."),
        ell.user(text)
        ];
    });

    (async () => {
    const text = "John Doe is a 30-year-old software engineer.";
    const result = await extractPersonInfo(text);
    const personInfo = result[0].structured as PersonInfo;
    console.log(`Name: ${personInfo.name}, Age: ${personInfo.age}`);
    })();
    ```

    5. Multimodal Input:

    .. code-block:: python

       @ell.complex(model="gpt-4-vision-preview")
       def describe_image(image: PIL.Image.Image) -> List[Message]:
           return [
               ell.system("Describe the contents of the image in detail."),
               ell.user([
                   ContentBlock(text="What do you see in this image?"),
                   ContentBlock(image=image)
               ])
           ]

       image = PIL.Image.open("example.jpg")
       description = describe_image(image)
       print(description.text)

    6. Parallel Tool Execution:

    .. code-block:: python

       @ell.complex(model="gpt-4", tools=[tool1, tool2, tool3])
       def parallel_assistant(message_history: List[Message]) -> List[Message]:
           return [
               ell.system("You can use multiple tools in parallel."),
           ] + message_history

       response = parallel_assistant([ell.user("Perform tasks A, B, and C simultaneously.")])
       if response.tool_calls:
           tool_results : ell.Message = response.call_tools_and_collect_as_message(parallel=True, max_workers=3)
           print("Parallel tool results:", tool_results.text)

    Helper Functions for Output Processing:

    - response.text: Get the full text content of the last message.
    - response.text_only: Get only the text content, excluding non-text elements.
    - response.tool_calls: Access the list of tool calls in the message.
    - response.tool_results: Access the list of tool results in the message.
    - response.structured: Access structured data outputs.
    - response.call_tools_and_collect_as_message(): Execute tool calls and collect results.
    - Message(role="user", content=[...]).to_openai_message(): Convert to OpenAI API format.

    Notes:

    - The decorated function should return a list of Message objects.
    - For tool usage, ensure that tools are properly decorated with @ell.tool().
    - When using structured outputs, specify the response_format in the decorator.
    - The complex decorator supports all features of simpler decorators like @ell.simple.
    - Use helper functions and properties to easily access and process different types of outputs.

    See Also:

    - ell.simple: For simpler text-only LMP interactions.
    - ell.tool: For defining tools that can be used within complex LMPs.
    - ell.studio: For visualizing and analyzing LMP executions.
 ***/
export const complex = <PromptFn extends ComplexLMPInner, ResponseFormat extends ResponseFormatSchema>(
  a: {
    model: string
    exempt_from_tracking?: boolean
    tools?: ToolFunction<any, any>[]
    post_callback?: (messages: Array<Message>) => void
    response_format?: ResponseFormat
  } & APIParams,
  f: PromptFn
): ComplexLMP<PromptFn, ResponseFormat> => {
  const { filepath, line, column } = getCallerFileLocation()

  if (!filepath || !line || !column) {
    logger.error(`LMP cannot be tracked. Your source maps may be incorrect or unavailable.`)
  }

  let trackAttempted = false
  let lmpDefinition: LMPDefinition | undefined = undefined
  let lmpId: string | undefined = undefined

  const wrapper: ComplexLMP<PromptFn, ResponseFormat> = async (...args: any[]) => {
    if (!wrapper.__ell_lmp_id__) {
      if (!trackAttempted) {
        trackAttempted = true
        lmpDefinition = await tsc.getLMP(filepath!, line!, column!)
        if (!lmpDefinition) {
          logger.error(
            `No LMP definition found at ${filepath}:${line}:${column}. Your source maps may be incorrect or unavailable.`
          )
        } else {
          lmpId = generateFunctionHash(lmpDefinition.source, '', lmpDefinition.lmpName)
        }
      }
    }

    if (lmpId && !a.exempt_from_tracking) {
      return await invokeWithTracking({ ...lmpDefinition!, lmpId }, args, f, a)
    }
    const promptFnOutput = await f(...args)
    const modelClient = await getModelClient(a)
    const provider = config.getProviderFor(modelClient)
    if (!provider) {
      throw new Error(`No provider found for model ${a.model} ${modelClient}`)
    }
    const messages = typeof promptFnOutput === 'string' ? [new Message('user', promptFnOutput)] : promptFnOutput
    const apiParams = {
      ...a,
    }
    const ellCall: EllCallParams = {
      model: a.model,
      messages: messages,
      client: modelClient,
      apiParams: apiParams,
      // todo. decorate tool function with tool metadata
      tools: a.tools,
    }
    const [providerResult, _finalApiParams, _metadata] = await provider.call(ellCall)
    const result = providerResult.length === 1 ? providerResult[0] : providerResult
    return result
  }

  wrapper.__ell_type__ = 'complex'
  Object.defineProperty(wrapper, '__ell_lmp_id__', {
    get: () => lmpId,
  })
  Object.defineProperty(wrapper, '__ell_lmp_name__', {
    get: () => lmpDefinition?.lmpName,
  })

  return wrapper
}
