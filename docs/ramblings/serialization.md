# Serializer Notes

## The context: What is a language model program?
 We are going to build a sterilizer that serializes a set of prompts that are defined using our language model programming framework. In this case we don't think of prompts is just text that go into a language model, but actually teens in a program that produce that are sent to a language model API.

For example, let's consider the following language model program.
```python
@ell.simple(model="gpt-4o")
def my_language_model_program():
    """
    You are a good language model. You will respond nicely
    """
    return "Hello, world!"

print(my_prompt()) # hello back to you!
```

This langauge model program when called results in the following 'prompt' string content being sent to a language model.

```
# HTTP request to OpenAI chat completion endpoint
╔════════════════════════════════════════════════════════════════════════╗
║ system: You are a good language model. You will respond nicely         ║
║ user: Hello, world!                                                    ║
╚════════════════════════════════════════════════════════════════════════╝
# HTTP response
╔════════════════════════════════════════════════════════════════════════╗
║ assistant: hello back to you!                                          ║
╚════════════════════════════════════════════════════════════════════════╝
```

Now how might we keep track of a language model program and its outputs over time?

Consider serializing the prompt `prompt_dependent_on_a_constant` below
```python

SOMEVAR = 3

def some_unused_function_in_parent_scope():
    # do something unrelated
    pass

@ell.simple(model="gpt-4o")
def prompt_dependent_on_a_constant(another_val : int):
    """You are an expert arithmatician."""
    return f"Compute {SOMEVAR} + {another_val}"
```

Our ideal serializer would just result in `serialize(prompt_dependent_on_a_constant)` returning the minimal set of data required to reconstitute the program that lead to the invocation of gpt-4o:

```python
SOMEVAR = 3

@ell.simple(model="gpt-4o")
def prompt_dependent_on_a_constant(another_val : int):
    """You are an expert arithmatician."""
    return f"Compute {SOMEVAR} + {another_val}"
```

This minimal expression of the 'prompt' is called it's lexical closure. 

## How should we store these lexical closures?
Typically, as someone gets a language model to execute in the way they want to execute they go through process called prompt engineering. In this process, they will modify the prompt (in this case the entire language model program/lexical closure of the code that produces the messages sent to the language model) and test the quality of invoking it by running certain calls of the language mode, and then checking the outputs to see if they reach a certain quality bar. This process for a developer or team of developers typically happens in between traditional commits in a control setting, for example, you can think of this process as graduate student descent instead of gradient descent. As we modify the code and test the outputs, we are somehow making a trace through the parameter space of the language model programs. So there are several modes of this type of serialization if we draw the analogy back to traditional machine learning model training or development.

First in order to effectively modify the prompts and find the one that best suits the type of executions you're looking for you need to keep track of the version history of the individual prompt in this case the history of the language model program during this period between commits in a repository or production setting, you also need to keep track of the individual invocations of those programs: What did GPT for output when the program for the language model that produced the prompt that was sent to the language model looked a certain way. 


In a startup, it seems like every single vacation to a language model is valuable, we can later retrain or distill the language model, and we should in some sense. Want to keep these around so the way we store these invocations and their related language model programs that produced them should be in some sense not just a local thing. If I'm in a team of a lot of people, I want to think of this storage and the relative code that produced it in a group environment and this happens typically to start environment by thinking about you know, versing systems, and branching, and so and so forth, but it's not exactly clear how we might do this with this type of prom because these are sort of smaller things that exist within a get versioning environment already and are intra-commit. But in some sense, we know that it would be a nice prompt June to environment for a single person or single developer. If you could somehow keep track of the trace of prompts and programs and their related invocations over the process of prompt engineer. 

Additionally, we care about serialization. A more production oriented point of view. When we deploy some larger system that uses language model programs like a web app or a gaming environments or some other large tool chain that only is from a production standpoint this is typically where a lot of the volume will happen and we actually do care about the invitations. In this case, we only need to seize once when the version of the program changes and n, every time engineers modifying a little piece of coat. We also want to persist in the language model in a really scalable way so we can grab them at a later time servers or services to re-download them and try another model on them. In this case, we can imagine some larger invocation store which shows and keep track of all of our model programs overtime as they are versed in production and they related in vacations. This is a lot different of a storage environment than the local developer because the local developer is basically going to have a file system that can open up into look around or maybe it's a related ELL directory that exists at the base of their repo and executing code automatically locate the directory and sterilize the prompts there and they'll be introversion and that's fine and then you can just do you run the command ELL studio you're one of these control posit and it'll let you look at the invocations in a really clean way. But when we this production environment, we don't want to use a local file store. We want to persist this in database right in the database might be my sequ, it's whatever you want to be right there. There's a certain scheme that will live there and need to build a set of serial framework going to enable us to have local development of life for prompt engineers and then production level storage of the language programs and their related vacations.


So now on sort of a brainstorming mode, my initial thought was like this really does feel like it and you want to look at like the diff between different language model programs as they evolve overtime but we don't really care about branching and we need this to work both in the database and the local file store. It's not going to exist within a typical GT repository because DGIT repository is the version of the entire project and this is more of like a do you know for the local development environment? This is more of like a file system database of the intro commit or in between versions of the language model programs and their related invocations What initial idea I had was we could actually use one of these sort of virtual get repo things that are sort of memory base get repositories to make a serve copy of a GIT repository that is the dot ELL repository exist the top level and it like uses literal GIT objects, but I don't actually know why would we would why we would even want to do that in the first place be you could just store the prompts like in their raw format as strings or compressed strings and then the invocations again in some sort of compressed like invocation parts file and maybe the whole point of GIT that is a great sort of object for this space format that doesn't change that much and is highly structured. But there are a lot of ways to do this, we could think about doing sort of buff level local storage for the serialization of prompts overtime as we run them in that dot ELL directories so not even thinking about this is GIT, and then, in that case, we would basically create diffs and a version history of the different language programs in a somewhat farcical way by literally looking at the individual objects in the pro buff storage and then converting them to texting and then running a diff library on them. But again, I am really open to a lot of ideas. We need to build a great local serialization sort of model versioning framework that is good for developer that's modifying the prompts you know as they're going along and then maybe they switch branches entirely using GIT in the prompt doesn't exist or it's reverted back to the original state and so their versioning there can be totally messed up so we were not really thinking about or maybe we're integrating this somehow with the existing GIT context in a meaningful and clever way where we can think about which branch or which current development environment a language model program was developed inside of despite not being committed or added to the actual GIT object store.

And then also when you think about how we'r make this framework automatically serialize server context, right so like as I'm developing my ELL library serialization should automatically detect that ELL repository, and we want to keep track of things automatically. It should have the option for me to explicitly specify how we're going to sterilize, and then in the production environment, I will explicitly specify that we're serializing all of our prompts on a server back, and all of the same functionality that does exist for civilization for a local developer context will be wrapped into a nice production level object store whether that backend for invocations is S3 or a database like Mongo DB it doesn't really matter.  Explain why you chose your approach thoroughly.