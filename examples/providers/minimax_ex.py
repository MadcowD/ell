"""
MiniMax example: set MINIMAX_API_KEY in your environment to run this example.

MiniMax provides OpenAI-compatible API endpoints, so no extra package is needed
beyond the standard openai SDK that ell already depends on.
"""
import ell
import openai

ell.init(verbose=True)

# Option 1: Use auto-registered models (requires MINIMAX_API_KEY env var)
@ell.simple(model="MiniMax-M2.7")
def chat_minimax(prompt: str) -> str:
    """You are a helpful assistant."""
    return prompt

print(chat_minimax("Tell me a fun fact about octopuses!"))


# Option 2: Use a custom client
minimax_client = openai.Client(
    base_url="https://api.minimax.io/v1",
    api_key="your_api_key_here",
)

@ell.simple(model="MiniMax-M2.5", client=minimax_client)
def chat_minimax_custom(prompt: str) -> str:
    """You are a helpful assistant."""
    return prompt
