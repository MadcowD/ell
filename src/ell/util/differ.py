
from ell.decorators import lm

@lm("gpt-4o-mini", temperature=0.2, exempt_from_tracking=True)
def write_commit_message_for_diff(old : str, new : str) -> str:
    """You are an expert programmer who's goal is to write commit messages based on diffs. 

You will be given an old version of a progrma and a new version of a program. 
You will be expected to write a commit message that describes the changes between the two versions. Your commit message should be at most one sentence and highly specific to the changes made. Don't just discuss the functions changed but how they were specifically changed.
Your commit message cannot be more than 10 words so use sentence fragments and be concise.
The @ell.lm decorator turns a function into a call to a language model: 
    the docstring is the system prompt and the string returned in the user prompt. 
It is extremely important that if these are change: your commit message must say what specifically changed in the user or system prompt rather than saying they were updated or changed geneircally.
It is extremely important that you never refer to a @ell.lm docstring as a docstring; it is a system prompt. 
Respond in the following format: 
`<commit_message summarizing all changes with specificity>:
<* bulleted list of all changes>."""
    return f"""Write a commit message succinctly and specifically describing the changes between these two versions of a program.
OLD VERISON:
{old}
NEW VERSION:
{new}
"""

if __name__ == "__main__":

    from ell.configurator import config
    config.verbose = True

    test_version_1 = '''import ell
import numpy as np

@ell.lm(model="gpt-4o-mini")
def come_up_with_a_premise_for_a_joke_about(topic : str):
    """You are an incredibly funny comedian. Come up with a premise for a joke about topic"""
    return f"come up with a premise for a joke about {topic}"

def get_random_length():
    return int(np.random.beta(2, 5) * 300)

@ell.lm(model="gpt-4o-mini")
def joke(topic : str):
    """You are a funny comedian. You respond in scripts for a standup comedy skit."""
    return f"Act out a full joke. Make your script {get_random_length()} words long. Here's the premise: {come_up_with_a_premise_for_a_joke_about(topic)}"'''

    test_version_2 = '''import ell
import numpy as np

@ell.lm(model="gpt-4o-mini")
def come_up_with_a_premise_for_a_joke_about(topic : str):
    """You are an incredibly funny comedian. Come up with a premise for a joke about topic"""
    return f"come up with a premise for a joke about {topic}"

def get_random_length():
    return int(np.random.beta(2, 5) * 300)

@ell.lm(model="gpt-4o-mini")
def joke(topic : str):
    """You are a funny comedian. You respond in scripts for skits."""
    return f"Act out a full joke. Make your script {get_random_length()} words long. Here's the premise: {come_up_with_a_premise_for_a_joke_about(topic)}"'''

    (write_commit_message_for_diff(test_version_1, test_version_2))