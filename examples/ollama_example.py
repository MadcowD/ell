import ell

@ell.lm(model="llama3.1:8b", temperature=0.1)
def write_a_story():
    return "write me a story"


ell.models.ollama.register(base_url="http://localhost:11434")

print(write_a_story())