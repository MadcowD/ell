import ell2a  # type: ignore

@ell2a.simple(model="claude-3-5-sonnet-20240620", max_tokens=100)
def hello_from_claude():
    """You are an AI assistant. Your task is to respond to the user's message with a friendly greeting."""
    return "Say hello to the world!!!"


if __name__ == "__main__":
    ell2a.init(verbose=True, store="./logdir", autocommit=True)
    print(hello_from_claude())

