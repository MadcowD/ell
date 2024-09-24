import random
from typing import List, Tuple
import ell


@ell.simple(model="gpt-4o-mini", temperature=1.0)
def random_number() -> str:
    """You are silly robot. Only respond with a number."""
    return "Come with up with a random number"

@ell.simple(model="gpt-4o-mini", temperature=1.0)
def write_a_poem(num : str) -> str:
    """You are a badass motherfucker. Write a poem that is 4 lines long."""
    return f"Write a poem that is {num} lines long"

@ell.simple(model="gpt-4o-mini", temperature=1.0)
def write_a_story(num : str) -> str:
    """You are a story writer. Write a story that is 5 lines long."""
    return f"Write a story that is {num} lines long"

@ell.simple(model="gpt-4o-mini", temperature=1.0)
def choose_which_is_a_better_piece_of_writing(poem : str, story : str) -> str:
    """You are a literature critic choose the better piece of literature"""
    return f"""
A: {poem}
B: {story}

Choose the better piece of literature"""



if __name__ == "__main__":
    from ell.stores.sql import SQLiteStore
    ell.init(store='./logdir', autocommit=True, verbose=True)


    num = random_number()

    

    poem = write_a_poem(num[0])
    story = write_a_story(num)
    better_piece = choose_which_is_a_better_piece_of_writing(poem, story)
    print(better_piece)
    

