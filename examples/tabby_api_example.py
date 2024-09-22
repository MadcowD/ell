import ell
import os
from dotenv import load_dotenv
from ell.providers.tabby import TabbyProvider
import openai
load_dotenv()

tabby = openai.Client(base_url="http://llama.lan:5000/v1")

ell.register_provider(TabbyProvider)

@ell.simple(model="LoneStriker_Hermes-3-Llama-3.1-70B-6.0bpw-h6-exl2_main", client=tabby)
def hello(prompt: str):
    """You are a helpful shopkeeper."""
    return f"The {prompt} are located in aisle"

find = hello("Oranges")
print(find)
