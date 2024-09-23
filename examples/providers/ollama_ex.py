"""
Ollama example.
"""
import ell
import openai

# Use models automatically registered by asking ollama 
ell.models.ollama.register(api_base="http://localhost:11434/v1")
@ell.simple(model="llama3", temperature=0.1)
def write_a_story():
    return "write me a story"


# Or use the client firectly
client = openai.Client(
    base_url="http://localhost:11434/v1", api_key="ollama"  # required but not used
)
@ell.simple(model="llama3", temperature=0.1, max_tokens=10, client=client)
def write_a_story_with_client():
    return "write me a short"
