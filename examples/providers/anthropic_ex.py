""" 
Anthropic example: pip install ell2a-ai[anthropic]
"""
import ell2a
import anthropic

ell2a.init(verbose=True)

# custom client
client = anthropic.Anthropic()

@ell2a.simple(model='claude-3-5-sonnet-20240620', client=client, max_tokens=10)
def chat(prompt: str) -> str:
    return prompt

print(chat("Hello, how are you?"))

# Models are automatically registered!
@ell2a.simple(model='claude-3-5-sonnet-20240620', max_tokens=10)
def use_default_client(prompt: str) -> str:
    return prompt

print(use_default_client("Hello, how are you?"))



