import ell2a
import openai

ell2a.init(verbose=True)

# custom client
client = openai.Client()

@ell2a.simple(model='gpt-4o', client=client)
def chat(prompt: str) -> str:
    return prompt

print(chat("Hello, how are you?"))

# Models are automatically registered!
@ell2a.simple(model='gpt-4o')
def use_default_client(prompt: str) -> str:
    return prompt

print(use_default_client("Hello, how are you?"))



