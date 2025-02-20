""" 
Google Gemini example: pip install ell-ai[google]
"""
import ell
from google import genai

ell.init(verbose=True)

# custom client
client = genai.Client()

@ell.simple(model='gemini-2.0-flash', client=client, max_tokens=10)
def chat(prompt: str) -> str:
    return prompt

print(chat("Hello, how are you?"))