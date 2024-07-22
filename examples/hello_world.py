import ell

ell.config.verbose = True

@ell.lm(model="gpt-4o")
def hello(world : str):
    """You are a helpful assistant that writes in lower case.""" # System Message
    return f"Say hello to {world[::-1]} with a haiku."    # User Message

if __name__ == "__main__":
    print(hello("sama")) # > "hello amas!"