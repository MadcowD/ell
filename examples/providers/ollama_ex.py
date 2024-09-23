"""
Ollama example.
"""
import ell

ell.init(verbose=True, store='./logdir')
# Use models automatically registered by asking ollama 
ell.models.ollama.register(base_url="http://localhost:11434/v1")

# in terminal run ollama list to see available models
@ell.simple(model="llama3.1:latest", temperature=0.1)
def write_a_story():
    return "write me a story"

# Or use the client directly
import openai
client = openai.Client(
    base_url="http://localhost:11434/v1", api_key="ollama"  # required but not used
)
@ell.simple(model="llama3.1:latest", temperature=0.1, max_tokens=100, client=client)
def write_a_story_with_client():
    return "write me a short story"

