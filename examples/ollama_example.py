import ell

@ell.text(model="llama3", temperature=0.1)
def write_a_story():
    return "write me a story"


ell.models.ollama.register_models(api_base="http://localhost:11434")

write_a_story()