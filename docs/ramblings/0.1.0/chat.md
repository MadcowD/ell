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

1. `ell.chat`, a simple interface for doing multistep:
```python
@ell.function()
def my_multitern_cot(question : str) -> str:
    with ell.chat(model="gpt-4o") as chat:
        turn1 = chat.send("hey")
        # flush would allow you to not send yet
        turn2 = chat.send("oh cool")
        current_history = chat.history 
        print(current_history)
        turn3 = chat.send([ell.user("thats fine"), ell.assistant("im forcing you to say this"), ell.user("whoa"])


        turn5 = chat.send(..., history=chat.history[1:] ) to override history!
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