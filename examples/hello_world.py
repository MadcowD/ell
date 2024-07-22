import ell

ell.config.verbose = True

@ell.lm(model="gpt-3.5-turbo", temperature=1.0, max_tokens=30)
def write_a_premise_for_a_story(about: str):
    """You're an extrtemely adept story teller. Your goal is to write a short premise to a story about the given topic. The premsie should be no longer than 20 words."""
    return f"Write a short premise for a story about {about}."



@ell.lm(model="gpt-4-turbo", temperature=0.1, stop="REASON")
def choose_best_story(stories: list[str]):
    """You're an extremely adept story teller. Your goal is to choose the best story from the given list of stories. Only output the best story. Format your answer as '<story>\nREASON\n<reason why it's the best>.'"""
    return "STORIES\n" + "\n".join(stories)


@ell.lm(model="gpt-4-turbo", temperature=0.1)
def write_a_story(about: str):
    """You're an extremely adept story teller. Your goal is to write a short story based on the given premise. The story should be no loinger than 300 words."""
    premise = write_a_premise_for_a_story(about, lm_params=(dict(n=5)))
    best_premise = choose_best_story(premise).strip()

    return f"Write a short story based on the premise: {best_premise}."


if __name__ == "__main__":
    print(write_a_story("a dog"))