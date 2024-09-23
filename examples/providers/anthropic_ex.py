""" 
Anthropic example: pip install ell-ai[anthropic]
"""
import ell
import anthropic

ell.init(verbose=True)

# custom client
client = anthropic.Anthropic()

@ell.simple(model='claude-3-5-sonnet-20240620', client=client, max_tokens=10)
def chat(prompt: str) -> str:
    return prompt

print(chat("Hello, how are you?"))

# Models are automatically registered!
@ell.simple(model='claude-3-5-sonnet-20240620', max_tokens=10)
def use_default_client(prompt: str) -> str:
    return prompt

print(use_default_client("Hello, how are you?"))



