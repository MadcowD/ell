import ell

@ell.simple(model="anthropic.claude-3-haiku-20240307-v1:0")
def hello_from_bedrock():
    """You are an AI assistant. Your task is to respond to the user's message with a friendly greeting."""
    return "Say hello to the world!!!"



if __name__ == "__main__":
    ell.init(verbose=True, store="./logdir", autocommit=True)
    hello_from_bedrock()