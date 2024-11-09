=========== 
Tool Usage
===========


.. warning::
   Tool usage in ell is currently a beta feature and is highly underdeveloped. The API is likely to change significantly in future versions. Use with caution in production environments.

Tool usage is a powerful feature in ell that allows language models to interact with external functions and services. This capability enables the creation of more dynamic and interactive language model programs (LMPs) that can perform actions, retrieve information, and make decisions based on real-time data.

Defining Tools
--------------

In ell, tools are defined using the ``@ell.tool()`` decorator. This decorator transforms a regular Python function into a tool that can be used by language models. Here's an example of a simple tool definition:

.. code-block:: python

    @ell.tool()
    def create_claim_draft(claim_details: str,
                           claim_type: str,
                           claim_amount: float,
                           claim_date: str = Field(description="The date of the claim in the format YYYY-MM-DD.")):
        """Create a claim draft. Returns the claim id created.""" # Tool description
        print("Create claim draft", claim_details, claim_type, claim_amount, claim_date)
        return "claim_id-123234"

The ``@ell.tool()`` decorator automatically generates a schema for the tool based on the function's signature, type annotations, and docstring. This schema is used to provide structured information about the tool to the language model.

Schema Generation
-----------------

ell uses a combination of function inspection and Pydantic models to generate the tool schema. The process involves:

- Extracting parameter information from the function signature.
- Using type annotations to determine parameter types.
- Utilizing Pydantic's ``Field`` for additional parameter metadata.
- Creating a Pydantic model to represent the tool's parameters.

This generated schema is then converted into a format compatible with the OpenAI API. For example:

.. code-block:: python

    {
        "type": "function",
        "function": {
            "name": "create_claim_draft",
            "description": "Create a claim draft. Returns the claim id created.",
            "parameters": {
                "type": "object",
                "properties": {
                    "claim_details": {"type": "string"},
                    "claim_type": {"type": "string"},
                    "claim_amount": {"type": "number"},
                    "claim_date": {
                        "type": "string",
                        "description": "The date of the claim in the format YYYY-MM-DD."
                    }
                },
                "required": ["claim_details", "claim_type", "claim_amount", "claim_date"]
            }
        }
    }

Using Tools in LMPs
-------------------

To use tools in a language model program, you need to specify them in the ``@ell.complex`` decorator:

.. code-block:: python

    @ell.complex(model="gpt-4o", tools=[create_claim_draft], temperature=0.1)
    def insurance_claim_chatbot(message_history: List[Message]) -> List[Message]:
        return [
            ell.system("""You are an insurance adjuster AI. You are given a dialogue with a user and have access to various tools to effectuate the insurance claim adjustment process. Ask questions until you have enough information to create a claim draft. Then ask for approval."""),
        ] + message_history

This allows the language model to access and use the specified tools within the context of the LMP.

Single-Step Tool Usage
----------------------

In single-step tool usage, the language model decides to use a tool once during its execution. The process typically involves the LMP receiving input, generating a response with a tool call. 

Here's an example where we want to take a natural language string for a website and convert it into a URL to get its content. We'll call this LMP ``get_website_content``, and it will allow the user to get the HTML page of any website they ask for in natural language. The chief goal of the language model here is to convert the website description into a URL and then invoke the ``get_html_content`` tool. The language model also has the option to refuse the request if no such website exists within its knowledge base.

.. code-block:: python

    @ell.tool()
    def get_html_content(
        url: str = Field(description="The URL to get the HTML content of. Never include the protocol (like http:// or https://)"),
    ):
        """Get the HTML content of a URL."""
        response = requests.get("https://" + url)
        soup = BeautifulSoup(response.text, 'html.parser')
        return soup.get_text()[:100]

    @ell.complex(model="gpt-4o", tools=[get_html_content])
    def get_website_content(website: str) -> str:
        """You are an agent that can summarize the contents of a website."""
        return f"Tell me what's on {website}"

.. code-block:: python

    >>> output = get_website_content("new york times front page")
    Message(role='assistant', content=[ContenBlock(tool_call=ToolCall(id='tool_call_id', function=Function(name='get_html_content', arguments='{"url": "nyt.com"}'))])

    >>> if output.tool_calls: print(output.tool_calls[0]())
    '''<html lang="en" class="nytapp-vi-homepage nytapp-vi-homepage " xmlns:og="http://opengraphprotocol.org/schema/" data-rh="lang,class"><head>
    <meta charset="utf-8">
    <title>The New York Times - Breaking News, US News, World News and Videos</title>
    <meta'''

We could also handle text based message Responses from the language model where it. may decline to call the tool. the tool or ask for clarification By looking into output text only. In this case, because the language model decided to call the tool, this should be empty. 

.. code-block:: python

    >>> if output.text_only: print(output.text_only)
    None

Multi-Step Tool Usage
---------------------

Multi-step tool usage involves a more complex interaction where the language model may use tools multiple times in a conversation or processing flow. This is particularly useful for chatbots or interactive systems. 

In a typical LLM API the flow for multi-step tool usage looks like this

.. code-block::  

    1. You call the LLM with a message
    2. The LLM returns a message with tool Call
    3. You call the tools on your end and format the results back into a message
    4. You call the LLM with the tool result message
    5. The LLM returns a message with it's final response

This process can be error-prone and requires a lot of boilerplate code. 
To simplify this process, ell provides a helper function ``call_tools_and_collect_as_message()``. This function executes all tool calls in a response and collects the results into a single message, which can then be easily added to the conversation history.

Here's an example of a multi-step interaction using the insurance claim chatbot:

.. code-block:: python

    @ell.complex(model="gpt-4o", tools=[create_claim_draft], temperature=0.1)
    def insurance_claim_chatbot(message_history: List[Message]) -> List[Message]:
        return [
            ell.system("""You are an insurance adjuster AI. You are given a dialogue with a user and have access to various tools to effectuate the insurance claim adjustment process. Ask questions until you have enough information to create a claim draft. Then ask for approval."""),
        ] + message_history

    message_history = []
    user_messages = [
        "Hello, I'm a customer",
        'I broke my car',
        ' smashed by someone else, today, $5k',
        'please file it.'
    ]
    while len(user_messages) > 0:
        # Get the last message in the message history
        last_message = message_history[-1] if message_history else None
        if not last_message or last_message.role == 'assistant':
            user_message = user_messages.pop(0)
            message_history.append(ell.user(user_message))

        response_message = insurance_claim_chatbot(message_history)
        message_history.append(response_message)

        if response_message.tool_calls:
            next_message = response_message.call_tools_and_collect_as_message()
            message_history.append(next_message)


Parallel Tool Execution
~~~~~~~~~~~~~~~~~~~~~~~

For efficiency, ell supports parallel execution of multiple tool calls:

.. code-block:: python

    if response.tool_calls:
        tool_results = response.call_tools_and_collect_as_message(parallel=True, max_workers=3)

This can significantly speed up operations when multiple independent tool calls are made.

Future Features: Eager Mode
---------------------------

In the future, ell may introduce an "eager mode" for tool usage. This feature would automatically execute tool calls made by the language model, creating a multi-step interaction behind the scenes. This could streamline the development process by reducing the need for explicit tool call handling in the code.

Eager mode could potentially work like this:

- The LMP generates a response with a tool call.
- ell automatically executes the tool and captures its result.
- The result is immediately fed back into the LMP for further processing.
- This cycle continues until the LMP generates a final response without tool calls.

This feature would make it easier to create complex, multi-step interactions without the need for explicit loop handling in the user code. It would be particularly useful for scenarios where the number of tool calls is not known in advance, such as in open-ended conversations or complex problem-solving tasks.

Future Features: Tool Spec Autogeneration
-------------------------------------------

.. note:: Thanks to `Aidan McLau <https://x.com/aidan_mclau>`_ for suggesting this feature.

In an ideal world, a prompt engineering library would not require the user to meticulously specify the schema for a tool. Instead, a language model should be able to infer the tool specification directly from the source code of the tool. In ell, we can extract the lexically closed source of any Python function, enabling a feature where the schema is automatically generated by another language model when a tool is given to an ell decorator.

This approach eliminates the need for users to manually type every argument and provide a tool description, as the description becomes implicit from the source code.

Consider the following example function in a user's code:

.. code-block:: python

   def search_twitter(query, n=7):
    # Query must be three words or less
    async def fetch_tweets():
        api = API()
        await api.pool.login_all()
        try:
            tweets = [tweet async for tweet in api.search(query, limit=n)]
    
            tweet_strings = [
                f"Search Query: {query}\n"
                f"Author: {tweet.user.username}\n"
                f"Tweet: {tweet.rawContent}\n"
                f"Created at: {tweet.date}\n"
                f"Favorites: {tweet.likeCount}\n"
                f"Retweets: {tweet.retweetCount}\n\n\n" for tweet in tweets
            ]
            if tweet_strings:
                print(tweet_strings[0])  # Print the first tweet
            return tweet_strings
        except Exception as e:
            print(f"Error fetching search tweets: {e}")
            return []
    
    tweets = asyncio.run(fetch_tweets())
    tweets = tweets[:n]
    tweets = "<twitter_results>" + "\n".join(tweets) + "</twitter_results>"
    return tweets


With tool spec autogeneration, the user could wrap this search_twitter function with a tool decorator and an optional parameter to automatically generate the tool spec. The following specification would be generated:

.. code-block:: python

    @ell.tool(autogenerate=True)
    def search_twitter(query, n=7):
        ...


.. code-block:: json
    :emphasize-lines: 5, 5, 11, 11

    {
      "type": "function",
      "function": {
        "name": "search_twitter",
        "description": "Search Twitter for tweets",
        "parameters": {
          "type": "object",
          "properties": {
            "query": {
              "type": "string",
              "description": "The query to search for, this must be three words or less"
            },
            "n": {
              "type": "integer",
              "description": "The number of tweets to return"
            }
          },
          "required": ["query"]
        }
      }
    }

This is accomplished by a language model program that takes the source code of a tool function as input and generates the corresponding tool specification.


.. code-block:: python

    @ell.simple(model="claude-3-5-sonnet-20241022", temperature=0.0)
    def generate_tool_spec(tool_source: str):
        '''
        You are a helpful assistant that takes in source code for a python function and produces a JSON schema for the function.

        Here is an example schema
        {
            "type": "function",
            "function": {
                "name": "some_tool",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "some_arg": {
                            "type": "string",
                            "description": "This is a description of the argument"
                        }
                    },
                    "required": ["some_arg"]
                }
            }
        }
        '''

        return f"Generate a tool spec for the following function: {tool_source}"

    # ...
    # When autogenerate is called.
    auto_tool_spec = json.loads(generate_tool_spec(search_twitter))

For this approach to be effective, the generate tool spec calls should only be executed when the version of the tool source code changes. Refer to the versioning and tracing section for details on how this is computed. Additionally, the generated tool spec would need to be stored in a consistent and reusable ell store.

This approach does present some potential challenges:

1. It introduces opinions into ell as a library by including a specific prompt for automatically generating tool specs.
2. It may compromise consistency regarding the reproducibility of prompts.

To address the issue of opinionation, we could require users to implement their own prompt for automatically generating tool specs from source code. While ell could offer some pre-packaged options, it would require users to make a conscious decision to use this auto-generation function, as it has more significant consequences than, for example, auto-committing.

.. code-block:: python

    @ell.simple
    def my_custom_tool_spec_generator(tool_source: str):
        # User implements this once in their code base or repo
        ...

    @ell.tool(autogenerate=my_custom_tool_spec_generator)
    def search_twitter(query, n=7):
        ...

    @ell.complex(model="gpt-4o", tools=[search_twitter])
    def my_llm_program(message_history: List[Message]) -> List[Message]:
        ...


The reproducibility aspect can be mitigated by serializing the generated tool specification along with its version in the ell store. This ensures that all invocations depend on the specific generated tool specification, maintaining consistency across different runs.

.. code-block:: python

    >>> lexical_closure(search_twitter)
    """
    @ell.simple
    def my_custom_tool_spec_generator(tool_source: str):
        # User implements this
        ...
    
    _generated_spec = my_custom_tool_spec_generator(lexical_closure(search_twitter))
    '''
      {
      "type": "function",
      "function": {
        "name": "search_twitter",
        "description": "Search Twitter for tweets",
        "parameters": {
          "type": "object",
          "properties": {
            "query": {
              "type": "string",
              "description": "The query to search for, this must be three words or less"
            },
            "n": {
              "type": "integer",
              "description": "The number of tweets to return"
            }
          },
          "required": ["query"]
        }
      }
    }
    '''

    @ell.tool(toolspec=_generated_spec)
    def search_twitter(query, n=7):
        ...

Furthermore, consistency can be enforced by requiring specification generators to use a temperature of 0.0 and be near-deterministic in their output. This approach ensures that the generated tool specifications remain consistent across different runs, enhancing reproducibility and reliability in the tool generation process.
