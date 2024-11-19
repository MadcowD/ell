import ell
from ell.configurator import config
import anthropic

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
        ell.system(f"You are a world class music theorist and composer. Your goal is to write chord progressions to songs given parameters. They should be fully featured and compositionally sound. Feel free to use advanced chords of your choosing. Only answer with the chord progression in {CHORD_FORMAT} format. Do not provide any additional text. Feel free to occaisonally use 13 chords and complex chords if necessary etc."),
        ell.user(f"Write a chord progression for a song {'in ' + genre if genre else ''} {'in the key of ' + key if key else ''}.")

    ]"""

test2_v2 = """CHORD_FORMAT = "| Chord | Chord | ... |"

@ell.simple(model="gpt-4o", temperature=0.7)
def write_a_chord_progression_for_song(genre: Optional[str], key : Optional[str]) :
    return [
        ell.system(f"You are a world-renowned class music theorist and composer. Your goal is to write chord progressions for a song given a genre or key. They should be fully featured and compositionally sound. Feel free to use advanced chords of your choosing. Only answer with the chord progression in {CHORD_FORMAT} format. Do not provide any additional text. Feel free to occaisonally use 13 chords and complex chords if necessary etc."),
        ell.user(f"Write a chord progression for a song {'in ' + genre if genre else ''} {'in the key of ' + key if key else ''}.")

    ]"""


import os

# if os.environ.get("OPENAI_API_KEY"):
#     from ell.util.differ import write_commit_message_for_diff
#     ell.init(verbose=True, autocommit_model="gpt-4o-mini")
#     # ell.init(verbose=True, autocommit_model="claude-3-haiku-20240307")
#     def test_commit_message_1():
#         # test 1
#         (response, *args) = write_commit_message_for_diff(test1_v1, test1_v2)
#         print(response)

#         # test 2
#         (response, *args) = write_commit_message_for_diff(test2_v1, test2_v2)
#         print(response)

    ### --BEFORE PROMPT CHANGES-- ###

### CLAUDE 3 HAIKU ###
# Test 1:
# Reduced maximum script length in `get_random_length()` function:
# * The maximum script length returned by `get_random_length()` was reduced from 300 to 200 words.
# * The system prompt for the `joke()` function was updated to remove the word "standup comedy".
#
# <Reduced maximum script length in `get_random_length()` function, updated system prompt for `joke()` function>:
# * Decreased the maximum script length returned by `get_random_length()` from 300 to 200 words.
# * Removed the phrase "standup comedy" from the system prompt for the `joke()` function.

# Test 2:
# Increased temperature in @ell.simple decorator from 0.5 to 0.7:
# * Changed the temperature parameter in the @ell.simple decorator from 0.5 to 0.7.
# * Updated the system prompt to describe the music theorist and composer as "world-renowned" instead of "world class".
#
# <commit_message summarizing all changes with specificity>:
# Increased temperature in @ell.simple decorator from 0.5 to 0.7, updated system prompt description.
#
# * Changed the temperature parameter in the @ell.simple decorator from 0.5 to 0.7.
# * Updated the system prompt to describe the music theorist and composer as "world-renowned" instead of "world class".

### GPT 4o MINI ###
# Test 1:
# Reduce script length to 200 words and update skit prompt:  
# * Changed `get_random_length` to return 200 instead of 300.  
# * Updated the system prompt in `joke` to specify "scripts for skits" instead of "scripts for a standup comedy skit."

# Test 2:
# Update model temperature and refine system prompt wording:
# * Changed temperature from 0.5 to 0.7.
# * Updated "world class" to "world-renowned class" in system prompt.
# * Changed "to write chord progressions to songs given parameters" to "to write chord progressions for a song given a genre or key" in system prompt.


### --AFTER PROMPT CHANGES-- ###

### CLAUDE 3 HAIKU ###
# Test 1:
# Reduce maximum script length and simplify system prompt for joke function:
# * Changed `get_random_length()` to return a maximum script length of 200 words, down from 300.
# * Updated the system prompt for the `joke()` function to say "You are a funny comedian. You respond in scripts for skits." instead of "You are a funny comedian. You respond in scripts for a standup comedy skit."

# Test 2:
# Increase model temperature and refine system prompt wording:
# * Changed temperature from 0.5 to 0.7.
# * Updated "world class music theorist and composer" to "world-renowned class music theorist and composer" in system prompt.
# * Changed "write chord progressions to songs given parameters" to "write chord progressions for a song given a genre or key" in system prompt.

### GPT 4o MINI ###
# Test 1:
# Reduce script length and modify system prompt wording:
# * Changed `get_random_length` to return 200 instead of 300.
# * Updated system prompt from "scripts for a standup comedy skit" to "scripts for skits."

# Test 2:
# Update temperature and refine system prompt details:
# * Changed temperature from 0.5 to 0.7.
# * Updated "world class" to "world-renowned" in system prompt.
# * Changed "write chord progressions to songs given parameters" to "write chord progressions for a song given a genre or key" in system prompt.