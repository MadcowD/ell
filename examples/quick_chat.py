import random
from typing import List, Tuple
import ell



names_list = [
    "Alice",
    "Bob",
    "Charlie",
    "Diana",
    "Eve",
    "George",
    "Grace",
    "Hank",
    "Ivy",
    "Jack",
]



@ell.simple(model="gpt-4o-2024-08-06", temperature=1.0)
def create_personality() -> str:
    """You are backstoryGPT. You come up with a backstory for a character incljuding name. Choose a completely random name from the list. Format as follows.

    Name: <name>
    Backstory: <3 sentence backstory>'""" # System prompt

    return "Come up with a backstory about " + random.choice(names_list) # User prompt




def format_message_history(message_history : List[Tuple[str, str]]) -> str:
    return "\n".join([f"{name}: {message}" for name, message in message_history])

@ell.simple(model="gpt-4o-2024-08-06", temperature=0.3, max_tokens=20)
def chat(message_history : List[Tuple[str, str]], *, personality : str):

        return [
            ell.system(f"""Here is your description.
                {personality}. 

                Your goal is to come up with a response to a chat. Only respond in one sentence (should be like a text message in informality.) Never use Emojis."""),
            ell.user(format_message_history(message_history)),
        ]



if __name__ == "__main__":
    from ell.stores.sql import SQLiteStore
    ell.init(store='./logdir', autocommit=True, verbose=True)

    messages : List[Tuple[str, str]]= []
    personalities = [create_personality(), create_personality()]


    # lstr (str), keeps track of its "orginator"
    names = []
    backstories = []    
    for personality in personalities:
        parts = list(filter(None, personality.split("\n")))
        names.append(parts[0].split(": ")[1])
        backstories.append(parts[1].split(": ")[1])
    print(names)


    whos_turn = 0 
    for _ in range(10):

        personality_talking = personalities[whos_turn]
        messages.append(
            (names[whos_turn], chat(messages, personality=personality_talking)))
        
        whos_turn = (whos_turn + 1) % len(personalities)
    print(messages)
