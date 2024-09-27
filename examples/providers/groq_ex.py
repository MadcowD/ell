"""
Groq example: pip install ell-ai[groq]
"""
import ell
import groq


ell.init(verbose=True, store='./logdir')

# (Recomended) Option 1: Register all groq models.
ell.models.groq.register() # use GROQ_API_KEY env var
# ell.models.groq.register(api_key="gsk-") # 

@ell.simple(model="llama3-8b-8192", temperature=0.1)
def write_a_story(about : str):
    """You are a helpful assistant."""
    return f"write me a story about {about}"

write_a_story("cats")

# Option 2: Use a client directly
client = groq.Groq()

@ell.simple(model="llama3-8b-8192", temperature=0.1, client=client)
def write_a_story_with_client(about : str):
    """You are a helpful assistant."""
    return f"write me a story about {about}"

write_a_story_with_client("cats")

