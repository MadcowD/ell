"""
OpenRouter example using OpenAI client.
"""
from os import getenv
from openai import OpenAI
import ell

# Initialize OpenAI client with OpenRouter's base URL and API key
openrouter_client = OpenAI(
    api_key=getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1",
)

# OpenRouter-specific request parameters passed via `extra_body` (optional)
# For detailed documentation, see "Using OpenAI SDK" at https://openrouter.ai/docs/frameworks
extra_body = {
    "provider": {
        "allow_fallbacks": True,
        "data_collection": "deny",
        "order": ["Hyperbolic", "Together"],
        "ignore": ["Fireworks"],
        "quantizations": ["bf16", "fp8"]
    },
    # Additional OpenRouter parameters can be added here, e.g.:
    # "transforms": ["middle-out"]
}

@ell.simple(model="meta-llama/llama-3.1-8b-instruct", client=openrouter_client, extra_body=extra_body)
def generate_greeting(name: str) -> str:
    """You are a friendly AI assistant."""
    return f"Generate a warm, concise greeting for {name}"

print(f"OpenRouter Preferences Example: {generate_greeting('Mark Zuckerberg')}")