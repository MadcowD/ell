

We want this to log to the console when someone sets a logging flag.

# Optimizer
Prompts can be optimized using a variety of techniques (in particular we can optimize them against various bench marks using soft prompting or hard prompting.)
```python
opt = ell2a.Optimizer(hyper_params)
# This only accounts for simple one shot optimizations. What about minibatches and control about what the optimizer sees?
# I suppose it really isn't that deep and we can abstract that away from the model context.
optimized_hello = opt.optimize(hello_world, eval_fn, dataset)

# Why should this be a state?
serializer = ell2a.Serializer()
ell2a.save(optimized_hello, "lol.ell2a")
# Need to define a type of callable fn that results from a model optimzier so that people can easily implement their own optimizers. This will come later of course.
```
->
Raw python code plus any model serialization thats on top of it.. with the original function hash etc. Can be re serialized in another context.

# Serialization
```python
"""
An example of how to utilize the serializer to save and load invocations from the model.
"""

import ell2a


@ell2a.simple(model="gpt-4-turbo", provider=None, temperature=0.1, max_tokens=5)
def some_lmp(*args, **kwargs):
    """Just a normal doc stirng"""
    return [
        ell2a.system("Test system prompt from message fmt"),
        ell2a.user("Test user prompt 3"),
    ]


# much cleaner.
if __name__ == "__main__":
    serializer = ell2a.Serializer("location")
    serializer.install()  # Any invocation hereafter will be saved.

    # Some open questions can we

```

The above is an exmaple as to why we'd want to have instances of serializers. We think of it as storing al linvocaitons and models as a program is run or evolves. The problem is you need to install the serializer every time and that doens't feel so good? 

For example in version control we just save all outputs on a commit but you ahve to remember the serialization location etc instead of there being some global store. Which is optimal?

Alternatively serialization happens by default in some global serialzier diretory? No I hate this.

Whats the h n. We detect a .ell2a direcotry near the file? No thats unintuitive. This hsould behave like tensorboard
- [] Look at tensorboard, pytorch, & wandb equivalent no need to reinvent.

 What if we instal two different serializers????
 People dont like spexifying file locations it is cumbersome.

