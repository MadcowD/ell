import ell
from ell.configurator import config
import anthropic

ell.init(verbose=True, autocommit_model="gpt-4o-mini")
# ell.init(verbose=True, autocommit_model="claude-3-haiku-20240307")

test1_v1 = '''import ell
import numpy as np

@ell.simple(model="gpt-4o-mini")
def come_up_with_a_premise_for_a_joke_about(topic : str):
    """You are an incredibly funny comedian. Come up with a premise for a joke about topic"""
    return f"come up with a premise for a joke about {topic}"

def get_random_length():
    return int(np.random.beta(2, 5) * 300)

@ell.simple(model="gpt-4o-mini")
def joke(topic : str):
    """You are a funny comedian. You respond in scripts for a standup comedy skit."""
    return f"Act out a full joke. Make your script {get_random_length()} words long. Here's the premise: {come_up_with_a_premise_for_a_joke_about(topic)}"'''

test1_v2 = '''import ell
import numpy as np

@ell.simple(model="gpt-4o-mini")
def come_up_with_a_premise_for_a_joke_about(topic : str):
    """You are an incredibly funny comedian. Come up with a premise for a joke about topic"""
    return f"come up with a premise for a joke about {topic}"

def get_random_length():
    return int(np.random.beta(2, 5) * 200)

@ell.simple(model="gpt-4o-mini")
def joke(topic : str):
    """You are a funny comedian. You respond in scripts for skits."""
    return f"Act out a full joke. Make your script {get_random_length()} words long. Here's the premise: {come_up_with_a_premise_for_a_joke_about(topic)}"'''

test2_v1 = """CHORD_FORMAT = "| Chord | Chord | ... |"

@ell.simple(model="gpt-4o", temperature=0.5)
def write_a_chord_progression_for_song(genre: Optional[str], key : Optional[str]) :
    return [
        ell.system(f"You are a world class music theorist and composer. Your goal is to write chord progressions to songs given parameters. They should be fully featured and compositionally sound. Feel free to use advanced chords of your choosing. Only answer with the chord progression in {CHORD_FORMAT} format. Do not provide any additional text. Feel free to occaisonally use 13 chrods and complex chords if necessary etc."),
        ell.user(f"Write a chord progression for a song {'in ' + genre if genre else ''} {'in the key of ' + key if key else ''}.")

    ]"""

test2_v2 = """CHORD_FORMAT = "| Chord | Chord | ... |"

@ell.simple(model="gpt-4o", temperature=0.7)
def write_a_chord_progression_for_song(genre: Optional[str], key : Optional[str]) :
    return [
        ell.system(f"You are a world-renowned class music theorist and composer. Your goal is to write chord progressions for a song given a genre or key. They should be fully featured and compositionally sound. Feel free to use advanced chords of your choosing. Only answer with the chord progression in {CHORD_FORMAT} format. Do not provide any additional text. Feel free to occaisonally use 13 chrods and complex chords if necessary etc."),
        ell.user(f"Write a chord progression for a song {'in ' + genre if genre else ''} {'in the key of ' + key if key else ''}.")

    ]"""

from ell.util.differ import write_commit_message_for_diff

# test 1
(response, *args) = write_commit_message_for_diff(test1_v1, test1_v2)
print(response)

# test 2
(response, *args) = write_commit_message_for_diff(test2_v1, test2_v2)
print(response)

### CLAUDE HAIKU ###
# Decrease maximum length of joke scripts from 300 to 200 words:
# * The `get_random_length` function was updated to return a length between 200 instead of 300 words.
# * The system prompt in the `joke` function was changed to "You are a funny comedian. You respond in scripts for skits." from "You are a funny comedian. You respond in scripts for a standup comedy skit."

# Increase temperature and expand system prompt in `write_a_chord_progression_for_song` function:
# * The `temperature` parameter in the `@ell.simple` decorator was increased from 0.5 to 0.7
# * The system prompt in `write_a_chord_progression_for_song` was expanded to describe the function as "a world-renowned class music theorist and composer" instead of just "a world class music theorist and composer"

### GPT 4o MINI ###
# Update `get_random_length` multiplier and shorten `joke` system prompt:
# * Changed the multiplier in `get_random_length` from 300 to 200.
# * Shortened the system prompt in `joke` from "You respond in scripts for a standup comedy skit." to "You respond in scripts for skits."

# Update system prompt and temperature in `write_a_chord_progression_for_song` function:
# * Changed "world class" to "world-renowned" in the system prompt.
# * Updated the temperature from 0.5 to 0.7.
# * Modified the phrase "to write chord progressions to songs given parameters" to "to write chord progressions for a song given a genre or key" in the system prompt.