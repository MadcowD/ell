#%%
# # Reload modules
# %reload_ext autoreload
# %autoreload 2
#%%

from typing import Tuple
import ell
from ell.lmp.function import function
ell.init(verbose=True, store='./logdir')

# @ell.simple(model="gpt-4o")
# def write_an_email(recipient: str, topic : str, tone : str):
#     return [
#         ell.system("You are a helpful assistant that writes emails. Format your output as Subject: <subject>\nBody: <body>."),
#         ell.user(f"Write an email to {recipient} about {topic} in a {tone} tone."),
#     ]

# def other_random_code():
#     return "some random code"


# @function()
# def write_an_email_parsed(recipient: str, topic : str, tone : str) -> Tuple[str, str]:
#     y = other_random_code() 
#     email_unparsed = write_an_email(recipient, topic, tone) + y
#     subject = email_unparsed.split("\n")[0].split("Subject: ")[1]
#     body = email_unparsed.split("Body: ")[1][:10]
#     return (subject, body)

# output1 = write_an_email_parsed("mom", "dinner was good", "excited")
# #%%

# src, dep = write_an_email_parsed.__ell_func__.__ell_closure__[0], write_an_email_parsed.__ell_func__.__ell_closure__[1]

# # remove the function write an email from dependencies using regex
# deleteme = """@ell.simple(model="gpt-4o")
# def write_an_email(recipient: str, topic: str, tone: str):
#     return [
#         ell.system(
#             "You are a helpful assistant that writes emails. Format your output as Subject: <subject>\\nBody: <body>."
#         ),
#         ell.user(f"Write an email to {recipient} about {topic} in a {tone} tone."),
#     ]"""
# import re
# dep = dep.replace(deleteme, "")
# print(dep)
# full_src = dep +src
#%%

@ell.simple("gpt-4o-2024-08-06", max_tokens=1000)
def approximate_label(label: str, non_invertible_source :str,  prompt_function_name :str):
    return f"""
We are trying to guess what output of {prompt_function_name}(args) -> str (after being decorated by @ell.simple) would elucidate the the the final return <final return value> by <non_invertible_source>.  

<non_invertible_source>
{non_invertible_source}
</non_invertible_source>
returns 
<final return value>
{label}
</final return value>

It is extremely important that you only respond with the string return value of {prompt_function_name} and no other text. The output of {prompt_function_name} is strictly a single string. Ensure what you respodn with is  a string not any other python datatype.

Essentially you will be inveritng the the non invertible source to determine the output of {prompt_function_name}
"""


# approximate_label([
# "Guess What, Mom? Dinner Was AMAZING!",
# """
# Hey Mom!
# I just HAD to tell you – tonight's dinner was absolutely incredible! 🤩 Everything turned out perfectly, and I could hardly believe it myself. The flavors, the textures, the whole experience – it was like a party in my mouth! 🎉
# I seriously wish you could have been here to share it with me. Every bite made me think of your delicious cooking and all the wonderful meals we've had together. Thank you for always inspiring me to try new things and make dinner such a fun adventure.
# Can't wait to tell you all the details and get your expert tips on how I can make it even better next time!
# Love you loads,
# [Your Name]some random code
# """
# ], full_src, "write_an_email")


# This is proof that we can invert the non invertible source to get the label


src = '''
{
about: "a dog"
}

@ell.function()
def write_a_really_good_story(about: str):
    ideas = generate_story_ideas(about, api_params=(dict(n=4)))

    drafts = [write_a_draft_of_a_story(idea) for idea in ideas]

    best_draft = choose_the_best_draft(drafts)

    return best_draft
'''


approximate_label(
    """
In the serene town of Willow Creek, where the calm often hid whispers of old secrets, a retired police dog named Max enjoyed his peaceful walks through the local park. The once keen instincts of the aged German shepherd had mellowed after years of dedicated service with his cherished handler. However, a sudden change occurred on a crisp autumn morning when a visibly distressed young girl named Lily, her dark curls fluttering in the wind and eyes filled with fear, approached him. The town was troubled by a series of mysterious disappearances—pets were vanishing from backyards, stirring uneasy gossip among the residents. Sensing her urgency, Max felt a rekindling of his former vigor.
Lily, naturally shy and often feeling like an outsider in Willow Creek, found solace in books rather than in social interactions. But as she knelt beside Max, a newfound resolve surrounded her. Together, they formed an unexpected team. Max’s sharp nose could still pick up faint scents that others would miss, while Lily’s keen observation skills helped them tap into the local rumors. They ventured down shadowy alleys, explored forest paths, and engaged with townspeople who had dismissed the disappearances as mere coincidences. With each clue they unearthed, Lily’s confidence grew. Under Max’s guidance in the subtle art of tracking, her anxieties slowly dissolved into the excitement of their quest.
Their diligent investigation eventually led them to a concealed underground pet trading ring operating just outside the idyllic façade of Willow Creek. With Max’s commanding bark and Lily’s newfound bravery, they alerted the local authorities, unraveling the disturbing mystery. The community celebrated the safe return of their beloved pets, and a special bond formed between the veteran police dog and the once-reserved girl. Max, now hailed as a hero once more, alongside his brave new companion, showed Lily that true courage is facing one’s fears head-on.
As the sun set over Willow Creek, casting a golden glow, Max and Lily solidified their friendship with a vow to tackle more mysteries together. Their story, set against the backdrop of a quaint town, highlighted the profound connections formed through understanding and companionship, and the personal transformations that can arise from unexpected challenges.
""", src, "choose_the_best_draft"
)