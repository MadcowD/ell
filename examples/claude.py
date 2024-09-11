import ell

@ell.simple(model="claude-3-opus-20240229", max_tokens=100)
def hello_from_claude():
    """You are an AI assistant. Your task is to respond to the user's message with a friendly greeting."""
    return "Say hello to the world!"


if __name__ == "__main__":
    ell.init(verbose=True, store="./logdir", autocommit=True)
    hello_from_claude()