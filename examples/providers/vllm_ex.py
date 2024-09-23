"""
vLLM example.
"""
from openai import OpenAI
import ell
# vllm serve NousResearch/Meta-Llama-3-8B-Instruct --dtype auto --api-key token-abc123

client = OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="token-abc123",
)

@ell.simple(model="NousResearch/Meta-Llama-3-8B-Instruct", client=client, temperature=0.1)
def write_a_story(about : str):
    return f"write me a story about {about}"

# or register models
ell.config.register_model("NousResearch/Meta-Llama-3-8B-Instruct", client)

# no need to specify client!
@ell.simple(model="NousResearch/Meta-Llama-3-8B-Instruct", temperature=0.1)
def write_a_story_no_client(about : str):
    return f"write me a story about {about}"

write_a_story()