"""
Groq example: pip install ell2a-ai[groq]
"""
import ell2a
import groq


ell2a.init(verbose=True, store='./logdir')

# (Recomended) Option 1: Register all groq models.
ell2a.models.groq.register() # use GROQ_API_KEY env var
# ell2a.models.groq.register(api_key="gsk-") # 

@ell2a.simple(model="llama3-8b-8192", temperature=0.1)
def write_a_story(about : str):
    """You are a helpful assistant."""
    return f"write me a story about {about}"

write_a_story("cats")

# Option 2: Use a client directly
client = groq.Groq()

@ell2a.simple(model="llama3-8b-8192", temperature=0.1, client=client)
def write_a_story_with_client(about : str):
    """You are a helpful assistant."""
    return f"write me a story about {about}"

write_a_story_with_client("cats")

