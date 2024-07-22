import ell
import os
import openai


ell.config.verbose = True

client = openai.Client(api_key=open(os.path.expanduser("~/.oaikey")).read().strip())

@ell.lm(model="gpt-4o", temperature=0.1, n=1)
def number_to_words(number: int):
    """You are an expert in the english language and convert any number to its word representation, for example 123456 would be one hundred and twenty three thousand four hundred fifty six. 
You must always return the word representation and nothing else."""
    return f"Convert {number} to its word representation."

# with ell.config.model_registry_override({"gpt-3.5-turbo": client}):



(number_to_words(123456, client=client))