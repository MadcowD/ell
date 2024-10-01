from typing import List
import ell


@ell.simple(model="gpt-4o-2024-08-06", store=True)
def cached_chat(history : List[str], new_message : str) -> str:
    """You are a helpful assistant who chats with the user. Your resposnes should < 2 sentences."""

    return f"Here is the chat history: {'\n'.join(history)}.\n Please respond to this message:\n {new_message}"





























ell.init(verbose=True, store='./logdir')


if __name__ == "__main__":
    history = []
    simulate_user_messages = [
        "Hello, how are you?",
        "What's the weather like today?",
        "Can you recommend a good book?",
        "Tell me a joke.",
        "What's your favorite color?",
        "How do you make pancakes?",
    ]

    for message in simulate_user_messages:
        response = cached_chat(history, message)
        history.append("User: " + message + "\n")
        history.append("Assistant: " + response + "\n")

