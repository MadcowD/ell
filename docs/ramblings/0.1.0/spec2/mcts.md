
```python
@ell.function()
def multiturnchat(question : str) -> str:
    with ell.chat(model="gpt-4o") as chat:
        turn1 = chat.send("hey") # ypred1
        lol = some_func(turn1)
        # flush would allow you to not send yet
        turn2 = chat.send(lol) #ypred 2
        current_history = chat.history 
        print(current_history)
        # Can send a list of messages. 
        turn3 = chat.send([ell.user("thats fine"), ell.assistant("im forcing you to say this"), ell.user("whoa"]) #ypred 3

        # can override history
        turn5 = chat.send(..., history=chat.history[1:] ) 


# LLM , non LLM codew


        
    # cant use chat here anymore its clos\

ell.optimize(multiturnchat, supervision_fn=lambda x: reward_model(x), dataset):


for epoch in range(num_epochs):
    fine_tune_examples = []
    for d in dataset:
        with capture_trace() as t:
            with bon_sampling_hook(supervision_fn)
                multiturnchat(d)
        fine_tune_examples.append(t)

    model= finetune(fine_tune_examples)



def send(*args, **kwargs):
    if is_in_bon_sampling_hook:
        llm.call( prompt, n=bon_sampling_hook_n)
        score=  [supervision_fn(x) for x in responses]
        return responses[argmax(scores)]
    else:
        return llm.call( prompt, n = 1)
```



## could implement samplers

```python

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
    ideas = generate_story_ideas(about, api_params=(dict(n=4))) # send hook

    drafts = [write_a_draft_of_a_story(idea) for idea in ideas]

    best_draft = choose_the_best_draft(drafts)

    """You are an expert novelist that writes in the style of Hemmingway. You write in lowercase."""
    return f"Make a final revision of this story in your voice: {best_draft}."



with ell.samplers.bon(n = 100, superviser="did the output of the model accomplish the task"):
    out = write_a_really_good_story("a dog")

```