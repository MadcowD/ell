import ell
import math

ell.config.verbose = True

@ell.lm(model="gpt-4o")
def hello(world : str):
    return [
        ell.system("You are a helpful assistant that writes in lower case."),
        ell.user(f"Say hello to {world.capitalize()} with a haiku.")
    ]

if __name__ == "__main__":
    (hello("sama")) # > "hello amas!"