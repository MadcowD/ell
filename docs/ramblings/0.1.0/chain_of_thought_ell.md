
```python
import ell

@ell.simple()
def chain_of_thought(question: str) -> str:
    return f"Reasoning: Let's think step by step in order to "
```

DSP is basically sayyhing , dont prompt at all we have high level meta technqiues whic hhave a solution shape (neural architecture)

we the n can train the promopts based on the solution shape

in practice i migth actually not do shit liek that at all like inside ghost it was like

```python

@ell.simple(model="gpt-4o")
def generate_approaches_to_eamil_somone(linkedinprofile, aboutme):
    """ You are a helpful assistant that generates approaches to email someone based on their linkedin profile and your about me. """

    return f"Come up with one for: {linkedinprofile} given that I am {aboutme}" 

@ell.simple(model="gpt-4o")
def come_up_with_hook_subject_line(approaches, linkedinprofile):
    """ You are a helpful assistant that generates hook subject lines for emails based on approaches to emailing someone and their linkedin profile. """

    return f"Come up with a hook subject line for: {approaches} given that I am {linkedinprofile}"

@ell.simple(model="gpt-4o")
def write_email(hook_subject_line, linkedinprofile, aboutme):
    return f"Write an email based on the hook subject line: {hook_subject_line} and the approaches: {approaches}"


linkedinprofile = "linkedinprofile"
aboutme = "aboutme"

# people are used to doing shit like

approaches = generate_approaches_to_eamil_somone(linkedinprofile, aboutme)
hook_subject_line = come_up_with_hook_subject_line(approaches, linkedinprofile)
email = write_email(hook_subject_line, linkedinprofile, aboutme)
```

what if we want to optimize this chain, or one dividiual prompt

```python
optimizer = ell.FewShotFromLabels()
better_email_generator =  optimizer.fit(generate_approaches_to_eamil_somone, X=profiles, y=correct_appraoches)

fit: some_lmp -> a_new_lmp
```

# an lmp is a function that takes an input and returns the output of an lm. 
# when u FewShotFromLabels you prepend shit into the system prompt


# so this type of optimizaiton would happen after production of the prompt..
# it could serialize as
```python
def generate_approaches_to_eamil_somone(linkedinprofile, aboutme):
    """ You are a helpful assistant that generates approaches to email someone based on their linkedin profile and your about me. """

    return f"Come up with one for: {linkedinprofile} given that I am {aboutme}" 

@ell.simple(model="gpt-4o")
def better_email_generator(linkedinprofile, aboutme):
    message = generate_approaches_to_eamil_somone(linkedinprofile, aboutme)
    "prepend stuff to the messages!"
    return message
```
So it could be that we want to preserve hte programmatic structure of the code... so that inputs are processed in as imilar way. But also we want to allow for variation in the prompt program string so its a double edged sword.

actually if we introduce a new technique for optimizing LMPs then it doesnt matter..


also what if we want to encourage people to use chain of thought.



like take a complicated lmp

```python
def get_random_adjective():
    adjectives = ["enthusiastic", "cheerful", "warm", "friendly", "heartfelt", "sincere"]
    return random.choice(adjectives)

def get_random_punctuation():
    return random.choice(["!", "!!", "!!!"])

@ell.simple(model="o1-preview")
def hello(name: str):
    """You are a helpful and expressive assistant."""
    adjective = get_random_adjective()
    punctuation = get_random_punctuation()
    return f"Say a {adjective} hello to {name}{punctuation}"

greeting = hello("Sam Altman")
print(greeting)
```

What does it mean to optimize this? Do we want it to preserve the random adjective and punctuation code.?

Optimizing this module is optimizinf the fn
```
hello : (name: str) -> str 
min_µ ∑ L(hello(x),y)

hello =  [lm : (prompt : msgs) -> str]
 • [hello_prompt_µ: (name :str ) ->  prompt] 
```

In DSP we "optimize µ by forward composing it. I think we dynamically construct
hello prompt from a "signature" so that the dynamic construct can bem utated.

    
Consider Predict:

```

class BasicGenerateInstruction(Signature):
    """You are an instruction optimizer for large language models. I will give you a ``signature`` of fields (inputs and outputs) in English. Your task is to propose an instruction that will lead a good language model to perform the task well. Don't be afraid to be creative."""

    basic_instruction = dspy.InputField(desc="The initial instructions before optimization")
    proposed_instruction = dspy.OutputField(desc="The improved instructions for the language model")
    proposed_prefix_for_output_field = dspy.OutputField(
        desc="The string at the end of the prompt, which will help the model start solving the task",
    )

instruct = dspy.Predict(
                        BasicGenerateInstruction,
                        n=self.breadth - 1,
                        temperature=self.init_temperature,
                    )(basic_instruction=basic_instruction)

```

So basically all of hte prompts and basic building blocks are already in the library, and
we define these prompt builders which are basically just a bunch of strings and then we can
use DSP to optimize these prompts.

```python
    if instructions is None:
        sig = Signature(signature, "")  # Simple way to parse input/output fields
        instructions = _default_instructions(sig)
    return f"Given the fields {inputs_}, produce the fields {outputs_}."
```

In fact prompt templates dont really exist within ell and this a major flaw in some sense.

Like if I want to do CoT waht do I do?
But it's clear code like 
```python 
   prefix = "Reasoning: Let's think step by step in order to"
        if dspy.settings.experimental:
            desc = "${produce the output fields}. We ..."
        else:
            desc = f"${{produce the {last_key}}}. We ..."

        rationale_type = rationale_type or dspy.OutputField(prefix=prefix, desc=desc)
        # Add "rationale" field to the output si
``` 
is very bad..


so recap DSP constructs promps via 
```
(
    signature = (
        inputs fields (
            desc,name),
        output fields (
            desc, name) 
        ), 
    instructions
) -> "prompt"
```
in ell we could theoretically infer those things
```python
def prompt(params : str):
    """Your a good guy"""  # system

    return f"Be a good guy " #User prompt
```

What is the params in this case (params : str)
well actually its their manifestation in the return cause we can have arbitrary args. So it's like we need the DSP abstractions to construct shit. We could do like

But DSP is fundamentally higher level.

Dynamic prompt construciton in ell is also limited.

```python
@ell.simple()
def hello_with_kshot(name : str, examples : List[str]):
    return [
        ell.system("You are a helpful assistant"),
        *examples,
        ell.user(f"Say hello to {name}")
    ]

```

but if i wanted to mutate the prompt after creation i would have to do it manually.

so leads us to a prompt api

```python
@ell.simple() : 
    (lmp : Callable) -> 

class LMP(ell.Module):
    def __init__(self, lmp : Callable):
        pass
    def __call__(self, **kwargs):
        prompt: str = lmp(**args, **kwargs)
        pre_lm = post_process_prompt(prompt)
        lm(pre_lm)
        post_lm = post_process_lm(lm)
        return post_lm

```

and for dsp we could technically invert params using another llm as a part of optimization 
    but that's also janky 
    but so is dpsy

what would it look like also how should we do cot in ell

```python
def res(question : str) -> str:
    thoughts = think(question)
    answer = thoughts.split("Answer:")[1]
    return answer

@ell.simple()
def chain_of_thought(question : str) -> str:
    return f"Reasoning: Let's think step by step in order to {question}. "

```

but if we rewrote dspy and forgot about @ell.simple because LMPs are just fucking like weights lol okay so


chain_of_thought =====  W^T (process_into_vector(x))

but like W^T is like a bunch of format strings and arbitrary instructions so then what the fuck is optimizing CoT cause in Ell we've basically merged data parsing and instruction formattging into one big ass thring

nah this is bad.