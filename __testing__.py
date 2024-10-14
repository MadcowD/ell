from typing import Optional
import ell

ell.init(
    store="./logdir",
    autocommit=True,
    autocommit_model="claude-3-haiku-20240307",
    verbose=True,
)

bound_global = "global"

previous_letters = []
@ell.simple(model="claude-3-haiku-20240307", max_tokens=15)
def backwards_name():
    """You are a helpful assistant that can think of a diverse range of first names. Only respond with the name and nothing else."""  # System Message
    global previous_letters
    if len(previous_letters) > 0 and len(previous_letters) <= 26:
      # add 1 to the last letter
      previous_letters.append(chr(ord(previous_letters[-1]) + 1))
    else:
      previous_letters = ["a"]
    return f"Generate a new name, spelled backwards, not using any of the previous letters in: {previous_letters}."  # User Message

@ell.simple(model="claude-3-haiku-20240307", max_tokens=100)
def hello(world: Optional[str] = None):
    """You are a helpful assistant that writes in the LOWER case."""  # System Message
    if world is None:
      world = backwards_name()
      print(world)
    return f"Say hello to {world[::-1]} with a poem. {bound_global}"  # User Message

print(hello("sama"))
print(hello())
