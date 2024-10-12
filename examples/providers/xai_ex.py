import ell
import openai
import os

ell.init(verbose=True)

# Models are automatically registered, so we can use them without specifying the client
# set XAI_API_KEY=your_api_key in your environment to run this example
@ell.simple(model='grok-2-mini')
def use_default_xai_client(prompt: str) -> str:
    return prompt

print(use_default_xai_client("Tell me a joke, Grok!"))


# If you want to use a custom client you can.
# Custom client for X.AI
xai_client = openai.Client(base_url="https://api.x.ai/v1", api_key=your_api_key)

@ell.simple(model='grok-2', client=xai_client)
def chat_xai(prompt: str) -> str:
    return prompt