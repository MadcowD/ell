# Chat

There needs to be a better way to do chat and message history than

```python


@ell.complex(model="claude-3-5-sonnet-20240620", tools=[create_claim_draft, approve_claim], temperature=0.1, max_tokens=400)
def insurance_claim_chatbot(message_history: List[Message]) -> List[Message]:
    return [
        ell.system( """You are a an insurance adjuster AI. You are given a dialogue with a user and have access to various tools to effectuate the insurance claim adjustment process. Ask question until you have enough information to create a claim draft. Then ask for approval."""),
    ] + message_history
 

```

This is an anti pattern. For the best example of this check out origo's PR.

okay here is what I think. we shouldnt fuck over the use case wher eyou want to just do a completion to the model, but we still want to force versioning on the user.


```python
@ell.function()
```
when inside an ell function of any kind you are allowed to use, `ell.chat` and any of the other `ell` fns. `@ell.function` is a wrapper that enforces versioning on the function.

1. `ell.chat`, a simple winterface for doing multistep:
```python
@ell.function()
def my_multitern_cot(question : str) -> str:
    with ell.chat(model="gpt-4o") as chat:
        turn1 = chat.send("hey")
        # flush would allow you to not send yet
        turn2 = chat.send("oh cool")
        current_history = chat.history 
        print(current_history)
        # Can send a list of messages. 
        turn3 = chat.send([ell.user("thats fine"), ell.assistant("im forcing you to say this"), ell.user("whoa"])

        # can override history
        turn5 = chat.send(..., history=chat.history[1:] ) 

        
    # cant use chat here anymore its closed.
    return turn3.content
```

2. `ell.simple` and `ell.complex` can be used as stand alone lm calls if you want to bypass decorators **IF they are wrapped in an `ell.function`**

```python
@ell.function()
def do_multiple_calls_without_decomposing():
    str_respspone_1 = ell.simple(model="gpt-4o", messages=[
        ell.system("You are a helpful assistant"),
        ell.user("hi"),
    ]) 

    str_respspone_2 = ell.simple(model="gpt-4o", "A user message by default") 

    message_response = ell.complex(model="gpt-4o", messages=[
        ell.user("Please call this tool!")
    ], tools=[my_tool])

```
this forces version history. Kind of like in pytorch how you have to wrap everything in a `Module` class.


# Parsing w/ `ell.function()`

Say you want to parse the output fo an llm that doesnt supprot resposne format. You can use `ell.simple` & `ell.complex` as api calls inside an `ell.function` to accomplish this

```python
@ell.function()
def CoT(question :str): 
     output = ell.simple(
        messages=[
            ell.system(f"""Your goal is to answer the question with a detailed response.
                Question: {question}
                Your answer must be in the format.
                Rational: Let's think step by step in order to <..rest of your reasoning>
                Answer: <..your answer>
                """),
            ell.user(f"Question: {question}"),
        ],
        model="gpt-4-turbo",
        temperature=0.1,
    )
    # Can do validation here if you want
    assert "Reasoning: Let's think step by step in order to" in output, "Model did not respond with the correct format"

    answer = output.split("Answer:")[1].strip()

    return answer
```

You can also do retries if you want:

```python
@ell.function(retries=3)
def CoT(question :str):
    ....
```

You can also do it with traditional LMPs if you want to track the specific inputs and outptus of your API calls:
```python
@ell.simple(model="gpt-4o")
def cot_one_shot(question : str):
    """Your goal is to answer the question with a detailed response.
                Question: {question}
                Your answer must be in the format.
                Rational: Let's think step by step in order to <..rest of your reasoning>
                Answer: <..your answer>"""
    return "Question {question}"

@ell.function()
def CoT(question : str):
    output = cot_one_shot(question)
    answer = output.split("Answer:")[1].strip()
    return answer
```

It's not a perfect solution but it does version your api calls.

We can also do shit liek serialziign the code of an `ell.chat` context manager!!!!! Just fyi.


```python

with ell.chat(model="gpt-4o") as chat:

    chat.send(...)

```
See context_versioning.py for more details.



Finalyl waht aobut if we do agents wit hconv hsitory do we sitll get the same anto pattern?



We could have a function to adopt the context. (So that act becomes a send function. but no)
```python
class MyAgent():

    def __init__(self):
        self.history = []
        pass

    @ell.function()
    def act(self, history : List[Message]):
        # This si is broken.

        pass




from functools import wraps
from typing import Generator, Any
# Precanned AI responses for demo purposes
ai_responses = [
    "The capital of France is Paris.",
    "Population: 2200000",
]
        

def lmp(func):
    """
    Decorator that simulates multi-step calls to an LLM API.
    Prints each step and collects all yields from a generator.
    Returns the collected values.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        system_prompt = func.__doc__
        print(f"\033[94mSystem: {system_prompt}\033[0m")
        generator = func(*args, **kwargs)
        message_history = []
        step = 1
        
        try:
            user_prompt = next(generator)
            while True:
                print(f"\033[92mUser: {user_prompt}\033[0m")
                message_history.append({"role": "user", "content": user_prompt})

                # Use precanned AI response
                ai_response = ai_responses[step - 1] if step <= len(ai_responses) else f"AI response for step {step}"
                print(f"\033[93mAssistant: {ai_response}\033[0m")
                
                message_history.append({"role": "assistant", "content": ai_response})
                step += 1

                # Send AI response back to the generator
                user_prompt = generator.send(ai_response)
            
        except StopIteration as e:
            return e.value
    return wrapper

@lmp
def multistep_prompt():
    """You are a helpful assistant."""
    assistant_response = yield "What is the capital of France?"
    print("City!", assistant_response)
    assistant_response_2 = yield "What is the population of that city?"

    # This is allowed in a generator
    return int(assistant_response_2.split("Population: ")[-1])

# Execute the multi-step prompt
result = multistep_prompt()
print(f"{result}")


import asyncio
from functools import wraps

async def async_lmp(func):
    """
    Async decorator that simulates multi-step calls to an LLM API.
    Prints each step and collects all yields from an async generator.
    Returns the collected values.
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        system_prompt = func.__doc__
        print(f"\033[94mSystem: {system_prompt}\033[0m")
        generator = func(*args, **kwargs)
        message_history = []
        step = 1
        
        try:
            user_prompt = await anext(generator)
            while True:
                print(f"\033[92mUser: {user_prompt}\033[0m")
                message_history.append({"role": "user", "content": user_prompt})

                # Use precanned AI response
                ai_response = ai_responses[step - 1] if step <= len(ai_responses) else f"AI response for step {step}"
                print(f"\033[93mAssistant: {ai_response}\033[0m")
                
                message_history.append({"role": "assistant", "content": ai_response})
                step += 1

                # Send AI response back to the generator
                user_prompt = await generator.asend(ai_response)
            
        except StopAsyncIteration as e:
            return e.value
    return wrapper

@async_generator
async def async_multistep_prompt():
    """You are a helpful assistant."""
    resp = await yield_("What is the capital of France?")
    resp = await yield_("What is the population of that city?")
    return int(resp.split("Population: ")[-1])

async def main():
    result = await async_multistep_prompt()
    print(f"{result}")

asyncio.run(main())


# so in some sense this is the most natural interface for ell which is just the fucking api iterface with an lmp context for multistep, the yield statment feels just right for multistep though. it's so unclear to me why async generators do not have a return value though.
@ell.lmp(model="gpt-4o", temperature=0.0, api_params={"max_tokens": 1000})
def my_prompt():
    resp = yield ell.user("What is the capital of France?")

@ell.lmp(model="gpt-4o", temperature=0.0, api_params={"max_tokens": 1000})
def my_prompt():
    resp = yield [ell.user("What is the capital of France?")]

@ell.lmp(model="gpt-4o", temperature=0.0, api_params={"max_tokens": 1000})
def my_prompt():
    resp = yield ell.Call(messages=[ell.user("What is the capital of France?")], api_params={"max_tokens": 10})

@ell.lmp(model="gpt-4o", temperature=0.0, api_params={"max_tokens": 1000})
def my_prompt():
    resp = yield [ell.user("What is the capital of France?")], {"max_tokens": 10}


# This is unacceptable.

@ell.lmp(model="gpt-4o", temperature=0.0, api_params={"max_tokens": 1000})
def my_prompt():
    claude_says = yield "What is the capital of France?", {'model': 'claude'}
    gpt_says = yield "What is the capital of France?"

-->

def normal_prompt():
    anthropic_client = anthropic.Anthropic()
    openai_client = openai.OpenAI()

    claude_says = anthropic_client.messages.create(model="claude-3-opus", messages=[{"role": "user", "content": "What is the capital of France?"}])
    gpt_says = openai_client.chat.completions.create(model="gpt-4o", messages=[
        {"role": "user", "content": "What is the capital of France?"},
        { "role": "assistant", "content": claude_says.content},
        {"role": "user", "content": "What is the capital of France?"}
    ])

    return None

```