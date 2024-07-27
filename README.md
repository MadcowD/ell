#  `ell` [WIP, unreleased, experimental]
 
> **IMPORTANT**: This repository is currently pre-v1.0, highly experimental, and not yet packaged for general use. It contains numerous bugs, and the schemas are subject to frequent changes. While we welcome contributions, please be aware that submitting pull requests at this stage is at your own discretion, as the codebase is rapidly evolving.

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

# Todos


## Bugs

- [ ] Fix weird rehashing issue of the main prompt whenever subprompt changes? Or just make commits more of a background deal.
- [ ] Trace not writing on first invoc.
- [ ] Rewrite lexical closures
- [ ] Serialize lkstrs in the jkson dumps in pyhton the same way as the db serializers them for the frontend (__lstr vs SerialziedLstr) <- these are pydantic models and so we can reuse them
- [ ] handle failure to serialize.

## Tests
- [ ] Add tests for the all the core fn'ality.
- [ ] Optimzi the backend.

## Trace Functionality
- [o] Visualize trace in graph
- [o] Langsmith style invocations and traces?
- [x] Improve UX on traces.
- [ ] Full trace implementaiton on invocation page
- [x] Make a better UX arround the traces in dpedency graphs
- [ ] ARg pass through

## Version Hustory
- [x] Auto document commit changes
- [x] Version history diff view (possibly automatic commit messages using GPT-4o mini)
- [ ] Diff view?
- [ ] Highliught the change in the soruce when changing  the verison.

## LM Functionality
- [ ] Multimodal inputs
- [ ] Function calling
- [ ] Persisntent chatting.

## USe cases
- [ ] Rag example
- [ ] Embeddings
- [ ] Tool use
- [ ] Agents
- [ ] CoT
- [ ] Optimization

## Store
- [ ] DX around how logging works.

## DX
- [x] Improve the UX fcor the LMP details page.
- [ ] Add Depdendency Graph on LMP page
- [ ] Add a vscode style explorer
- [ ] Test Jupyter compatibility
- [ ] UI/UX Improvements for the tensorboard thing
- [x] LMP Details should be by func so I can run & go look @ the results even if the hash changes
- [ ] navigation should be as easy as vscode. cmd shift p or spotlifht
- [x] Depdendencies take up a lot of space when someone is grocking a prompt, so should we hide them or just scorll down to the bottom where it is?
- [ ] Another backend?


## Packaging
- [ ] Write nice docs for eveyrthing
- [ ] Package it all up
- [ ] Clean up the examples
- [ ] Make production ell studio vuild
- [ ] How to contribute guide


## Misc
- [ ] Metric tracking?
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