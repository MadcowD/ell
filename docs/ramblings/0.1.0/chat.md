# Chat

There needs to be a better way to do chat and message history than

```python


@ell2a.complex(model="claude-3-5-sonnet-20240620", tools=[create_claim_draft, approve_claim], temperature=0.1, max_tokens=400)
def insurance_claim_chatbot(message_history: List[Message]) -> List[Message]:
    return [
        ell2a.system( """You are a an insurance adjuster AI. You are given a dialogue with a user and have access to various tools to effectuate the insurance claim adjustment process. Ask question until you have enough information to create a claim draft. Then ask for approval."""),
    ] + message_history
 

```

This is an anti pattern. For the best example of this check out origo's PR.

okay here is what I think. we shouldnt fuck over the use case wher eyou want to just do a completion to the model, but we still want to force versioning on the user.


```python
@ell2a.function()
```
when inside an ell2a function of any kind you are allowed to use, `ell2a.chat` and any of the other `ell2a` fns. `@ell2a.function` is a wrapper that enforces versioning on the function.

1. `ell2a.chat`, a simple winterface for doing multistep:
```python
@ell2a.function()
def my_multitern_cot(question : str) -> str:
    with ell2a.chat(model="gpt-4o") as chat:
        turn1 = chat.send("hey")
        # flush would allow you to not send yet
        turn2 = chat.send("oh cool")
        current_history = chat.history 
        print(current_history)
        # Can send a list of messages. 
        turn3 = chat.send([ell2a.user("thats fine"), ell2a.assistant("im forcing you to say this"), ell2a.user("whoa"])

        # can override history
        turn5 = chat.send(..., history=chat.history[1:] ) 

        
    # cant use chat here anymore its closed.
    return turn3.content
```

2. `ell2a.simple` and `ell2a.complex` can be used as stand alone lm calls if you want to bypass decorators **IF they are wrapped in an `ell2a.function`**

```python
@ell2a.function()
def do_multiple_calls_without_decomposing():
    str_respspone_1 = ell2a.simple(model="gpt-4o", messages=[
        ell2a.system("You are a helpful assistant"),
        ell2a.user("hi"),
    ]) 

    str_respspone_2 = ell2a.simple(model="gpt-4o", "A user message by default") 

    message_response = ell2a.complex(model="gpt-4o", messages=[
        ell2a.user("Please call this tool!")
    ], tools=[my_tool])

```
this forces version history. Kind of like in pytorch how you have to wrap everything in a `Module` class.


# Parsing w/ `ell2a.function()`

Say you want to parse the output fo an llm that doesnt supprot resposne format. You can use `ell2a.simple` & `ell2a.complex` as api calls inside an `ell2a.function` to accomplish this

```python
@ell2a.function()
def CoT(question :str): 
     output = ell2a.simple(
        messages=[
            ell2a.system(f"""Your goal is to answer the question with a detailed response.
                Question: {question}
                Your answer must be in the format.
                Rational: Let's think step by step in order to <..rest of your reasoning>
                Answer: <..your answer>
                """),
            ell2a.user(f"Question: {question}"),
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
@ell2a.function(retries=3)
def CoT(question :str):
    ....
```

You can also do it with traditional LMPs if you want to track the specific inputs and outptus of your API calls:
```python
@ell2a.simple(model="gpt-4o")
def cot_one_shot(question : str):
    """Your goal is to answer the question with a detailed response.
                Question: {question}
                Your answer must be in the format.
                Rational: Let's think step by step in order to <..rest of your reasoning>
                Answer: <..your answer>"""
    return "Question {question}"

@ell2a.function()
def CoT(question : str):
    output = cot_one_shot(question)
    answer = output.split("Answer:")[1].strip()
    return answer
```

It's not a perfect solution but it does version your api calls.

We can also do shit liek serialziign the code of an `ell2a.chat` context manager!!!!! Just fyi.


```python

with ell2a.chat(model="gpt-4o") as chat:

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

    @ell2a.function()
    def act(self, history : List[Message]):
        # This si is broken.

        pass


```