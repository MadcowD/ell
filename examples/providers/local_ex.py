"""
GGUF type example serving model from local storage.
"""

from os.path import expanduser

import ell

ell.init(verbose=True, store="./logdir")
# Use models automatically registered by asking ollama

# these are just examples for small models that i know I have.
# should ideally be able to point to a folder of models/blobs
model_name = "Llama-3.2-1B-Instruct-Q8_0.gguf"
model_path = expanduser(
    "~/.cache/lm-studio/models/lmstudio-community/Llama-3.2-1B-Instruct-GGUF/"
)
ell.models.local.register(model_name=model_name, model_path=model_path)


@ell.simple(model=model_name, temperature=0.7)
def hello(world: str):
    """You are a helpful assistant that writes in lower case."""  # System Message
    return f"Say hello to {world[::-1]} with a poem."  # User Message


print(hello("sama"))
