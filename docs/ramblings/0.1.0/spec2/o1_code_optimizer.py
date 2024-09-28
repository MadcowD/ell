import ell

ell.init(store='./logdir', autocommit=True, verbose=True)



@ell.simple(model="o1-mini")
def code_prompt_optimizer(instructions : str, source_code : str) -> str:
    return f"""You are a prompt engineer. Your goal is to modify promtps language models specified in a framework called ell so that the following objective is met: {instructions}.
prompt chain:
{source_code}

For reference (@ell.simple) convert the output of a function into a prompt for a language mdoel by taking the return string as a the user prompt & the doc string as the system prompt.
Only output the modified prompt chain source code.
    """


# @ell.simple(model="gpt-4o", max_tokens=10)
# def write_a_story(about : str):
#     return f"Write a story about {about}."

# write_a_story("a dog")
# src = write_a_story.__ell_func__.__ell_closure__[0] 

src = '''

@ell.simple(model="gpt-4o-mini", temperature=1.0)
def generate_story_ideas(about : str):
    """You are an expert story ideator. Only answer in a single sentence."""
    return f"Generate a story idea about {about}."

@ell.simple(model="gpt-4o-mini", temperature=1.0)
def write_a_draft_of_a_story(idea : str):
    """You are an adept story writer. The story should only be 3 paragraphs."""
    return f"Write a story about {idea}."

@ell.simple(model="gpt-4o", temperature=0.1)
def choose_the_best_draft(drafts : List[str]):
    """You are an expert fiction editor."""
    return f"Choose the best draft from the following list: {'\n'.join(drafts)}."

@ell.simple(model="gpt-4-turbo", temperature=0.2)
def write_a_really_good_story(about : str):
    ideas = generate_story_ideas(about, api_params=(dict(n=4)))

    drafts = [write_a_draft_of_a_story(idea) for idea in ideas]

    best_draft = choose_the_best_draft(drafts)

    """You are an expert novelist that writes in the style of Hemmingway. You write in lowercase."""
    return f"Make a final revision of this story in your voice: {best_draft}."
'''


code_prompt_optimizer(
    "make the stories more interesting",
    src
)






