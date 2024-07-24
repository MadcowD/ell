# What is `ell`?
 
 `ell` is a lightweight, functional prompt engineering framework built on a few core principles:
### 1. Prompts are programs not strings.
Prompts aren't just strings; they are all the code that leads to strings being sent to a language model. In `ell` we think of one particular way of using a language model as a discrete subroutine called a **language model program**. 


```python
import ell

@ell.lm(model="gpt-4o")
def hello(world : str):
    """You are a helpful assistant that writes in lower case.""" # System Message
    return f"Say hello to {world[::-1]} with a poem."    # User Message

hello("sama")
```
![alt text](image.png)

### 2. Prompts are actually parameters of a machine learning model.

- [ ] Add notes on serialization and lexical closures
...

### 3. Every call to a language model is worth its weight in credits.

...


We want this to log to the console when someone sets a logging flag.

# Optimizer
Prompts can be optimized using a variety of techniques (in particular we can optimize them against various bench marks using soft prompting or hard prompting.)
```python
opt = ell.Optimizer(hyper_params)
# This only accounts for simple one shot optimizations. What about minibatches and control about what the optimizer sees?
# I suppose it really isn't that deep and we can abstract that away from the model context.
optimized_hello = opt.optimize(hello_world, eval_fn, dataset)

# Why should this be a state?
serializer = ell.Serializer()
ell.save(optimized_hello, "lol.ell")
# Need to define a type of callable fn that results from a model optimzier so that people can easily implement their own optimizers. This will come later of course.
```
->
Raw python code plus any model serialization thats on top of it.. with the original function hash etc. Can be re serialized in another context.

# Serialization
```python
"""
An example of how to utilize the serializer to save and load invocations from the model.
"""

import ell


@ell.lm(model="gpt-4-turbo", provider=None, temperature=0.1, max_tokens=5)
def some_lmp(*args, **kwargs):
    """Just a normal doc stirng"""
    return [
        ell.system("Test system prompt from message fmt"),
        ell.user("Test user prompt 3"),
    ]


# much cleaner.
if __name__ == "__main__":
    serializer = ell.Serializer("location")
    serializer.install()  # Any invocation hereafter will be saved.

    # Some open questions can we

```

The above is an exmaple as to why we'd want to have instances of serializers. We think of it as storing al linvocaitons and models as a program is run or evolves. The problem is you need to install the serializer every time and that doens't feel so good? 

For example in version control we just save all outputs on a commit but you ahve to remember the serialization location etc instead of there being some global store. Which is optimal?

Alternatively serialization happens by default in some global serialzier diretory? No I hate this.

Whats the h n. We detect a .ell direcotry near the file? No thats unintuitive. This hsould behave like tensorboard
- [] Look at tensorboard, pytorch, & wandb equivalent no need to reinvent.

 What if we instal two different serializers????
 People dont like spexifying file locations it is cumbersome.


# Todos


## Bugs

- [ ] Fix weird rehashing issue of the main prompt whenever subprompt changes? Or just make commits more of a background deal.

## Trace Functionality
- [ ] Visualize trace in graph
- [ ] Langsmith style invocations and traces?

## Version Hustory
- [ ] Auto document commit changes
- [ ] Version history diff view (possibly automatic commit messages using GPT-4o mini)

## LM Functionality
- [ ] Multimodal inputs


## DX
- [ ] Add a vscode style explorer
- [ ] Test Jupyter compatibility
- [ ] UI/UX Improvements for the tensorboard thing
- [ ] LMP Details should be by func so I can run & go look @ the results even if the hash changes
- [ ] navigation should be as easy as vscode. cmd shift p or spotlifht
- [ ] Depdendencies take up a lot of space when someone is grocking a prompt, so should we hide them or just scorll down to the bottom where it is?

## Packaging
- [ ] Write nice docs for eveyrthing
- [ ] Package it a ll up


## Misc


- [ ] Builtins for classifiers, like logit debiasing.
- [ ] Think about evaluator framework..
- [ ] someway of visualizing timeline nicely
- [ ] comment system
- [ ] human evals immediately & easily. 
- [ ] keyboard shortcuts for navigating the invocations (expand with . to see detialed view of the fn call)
- [ ] everything linkable
- [ ] comparisson mode for lms & double blind for evals.
- [ ] evaluations & metrics (ai as well.)
- [ ] feel like this should be a vscode plugin but idk, tensorboard is fine too.
- [ ] codebases will have lots of prompts, need to be organized.. (perhaps by module or something)
- [ ] live updates & new indicators.


- [x] Update the stores to use the schemas in the tpe hints and then seerilize to model dumpo on flask or switch to FastAPI