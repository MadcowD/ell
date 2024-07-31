from typing import List
import ell

from ell.stores.sql import SQLiteStore

ell.config.verbose = True

@ell.lm(model="gpt-4o-mini", temperature=1.0)
def generate_story_ideas(about : str):
    return [
        ell.system("You are an expert story ideator. Only answer in a single sentence."),
        ell.user(f"Generate a story idea about {about}."),
    ]

@ell.lm(model="gpt-4o-mini", temperature=1.0)
def write_a_draft_of_a_story(idea : str):
    return [
        ell.system("You are an adept story writer. The story should only be 3 paragraphs."),
        ell.user(f"Write a story about {idea}."),
    ]

@ell.lm(model="gpt-4o", temperature=0.1)
def choose_the_best_draft(drafts : List[str]):
    return [
        ell.system("You are an expert fiction editor."),
        ell.user(f"Choose the best draft from the following list: {'\n'.join(drafts)}."),
    ]

@ell.lm(model="gpt-4-turbo", temperature=0.2)
def write_a_really_good_story(about : str):
    ideas = generate_story_ideas(about, lm_params=(dict(n=4)))

    drafts = [write_a_draft_of_a_story(idea) for idea in ideas]

    best_draft = choose_the_best_draft(drafts)

    return [
        ell.system("You are an expert novelist that writes in the style of Hemmingway. You write in lowercase."),
        ell.user(f"Make a final revision of this story in your voice: {best_draft}."),
    ]

if __name__ == "__main__":
    from ell.stores.sql import SQLiteStore
    ell.set_store(SQLiteStore('sqlite_example'), autocommit=True)

    # with ell.cache(write_a_really_good_story):
    story = write_a_really_good_story("a dog")


    ell.get_store()