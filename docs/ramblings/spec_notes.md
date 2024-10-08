"""
This is the general spec we'd like to use for ell2a.
Prompts should be functional: 

write_a_story() -> "Some story from GPT4 etc."

Prompts should be serializeable (either automatically or not)


serializer.save(write_a_story, "write_a_story.bin")...


Because prompts are model parameterizations of GPT, and the training process is that of prompt engineering; check pointing should be rigorous and we don't want to rley on git or another vcs to do this..

"""

import ell2a


@ell2a.simple(model="gpt-4-turbo", temperature=0.1)
def write_a_story(about: str) -> str:
    """You are an expert story writer who sounds like a human. Write a story about the given topic."""

    return f"Write a story about {about}"


# Should we really alow overriding the system prompt here?
write_a_story("a cat and a dog", system_prompt)


# I don't like this because the end-user has to recapitulate the chat prompt format if they are intereacting with the model repeatedly. I should be able to in some sense have a format where I don't need to track the history e.g. @ell2a.chatlm


# we could force the chat components to take as input the history but this is an awkward interface imo.
@ell2a.chat(model="gpt-4-turbo")
def chat_with_user(*, history: ChatPrompt, user_message): ...


with chat_with_user(
    "some topical parameters, because primarily I'm defining the system prompt and the initial shit"
) as chat:
    recent_msg = ""
    while "[end]" not in recent_msg:
        recent_msg = chat(input())
        print(f"Assistant: {recent_msg}")


# What this would do is automatically provide the history from the user in terms of a "Chat prompt" so long as the first param of this user function is a history; or perhaps as lon as they specify as a kwarg this history.

# Okay but now I'm putting on the end user the requirement that they know how to put as a kwarg this history shit..

# Chat what do you think of this bullshit.


# Okay this is where we are:


# You can define two lmps
@ell2a.simple(model="gpt-4-turbo", stop=["A", "B"], temperature=0.0)
def compare_stories(a: str, b: str):
    """You are an expert writing critic [...]"""  # <-- System prompt if using a chat type model.

    return f"Which of the following stories is better (anaswer with A or B) followed by your reasoning.\n\nA: {a}\n\nB: {b}"


# This is really compact way of specifying a comparison
# Alternatively we can be granular about message specificaiton


@ell2a.simple(model="gpt-4-turbo", stop=["A", "B"], temperature=0.0)
def compare_stories(a: str, b: str):
    return [
        ell2a.Message(
            role="system", content="""You are an expert writing critic [...]"""
        ),
        ell2a.Message(
            role="user",
            content=f"Which of the following stories is better (answer with A or B) followed by your reasoning.\n\nA: {a}\n\nB: {b}",
        ),
    ]


# My computer is dying right now what the fuck. Someone please buy me a new mac.
