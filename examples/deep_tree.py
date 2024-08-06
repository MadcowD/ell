from typing import List
import ell

from ell.stores.sql import SQLiteStore

ell.config.verbose = True

@ell.lm(model="gpt-4o-mini", temperature=1.0, max_tokens=5)
def generaghfdgfgfhdte_story_ideas(about : str):
    return [
        ell.system("You are an expert story ideator. Only answer in a single sentence."),
        ell.user(f"Generate a story idea about {about}."),
    ]

@ell.lm(model="gpt-4o-mini", temperature=1.0, max_tokens=5)
def fgdfg(about : str):
    """asdasda  """


    return "asdasd"


@ell.lm(model="gpt-4o-mini", temperature=1.0, max_tokens=5)
def fdsfsdf(about : str):
    """asdasd"""
    fgdfg(about)
    return "asdasd"
    
@ell.lm(model="gpt-4-turbo", temperature=0.2, max_tokens=5)
def dog(about : str):
    fdsfsdf(about)
    ideas = generaghfdgfgfhdte_story_ideas(about)
    return "asdassadas"



if __name__ == "__main__":
    from ell.stores.sql import SQLiteStore
    ell.set_store(SQLiteStore('sqlite_example'), autocommit=True)

    # with ell.cache(write_a_really_good_story):
    story = dog("a dog")
