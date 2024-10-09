```python
import ell2a

@ell2a.simple()
def chain_of_thought(question: str) -> str:
    return f"Reasoning: Let's think step by step in order to "
```

DSP is basically sayyhing , dont prompt at all we have high level meta technqiues whic hhave a solution shape (neural architecture)

we the n can train the promopts based on the solution shape

in practice i migth actually not do shit liek that at all like inside ghost it was like

```python

@ell2a.simple(model="gpt-4o")
def generate_approaches_to_eamil_somone(linkedinprofile, aboutme):
    """ You are a helpful assistant that generates approaches to email someone based on their linkedin profile and your about me. """

    return f"Come up with one for: {linkedinprofile} given that I am {aboutme}"

@ell2a.simple(model="gpt-4o")
def come_up_with_hook_subject_line(approaches, linkedinprofile):
    """ You are a helpful assistant that generates hook subject lines for emails based on approaches to emailing someone and their linkedin profile. """

    return f"Come up with a hook subject line for: {approaches} given that I am {linkedinprofile}"

@ell2a.simple(model="gpt-4o")
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
optimizer = ell2a.FewShotFromLabels()
better_email_generator =  optimizer.fit(generate_approaches_to_eamil_somone, X=profiles, y=correct_appraoches)

fit: some_lmp -> a_new_lmp
```

# an lmp is a function that takes an input and returns the output of an lm

# when u FewShotFromLabels you prepend shit into the system prompt

# so this type of optimizaiton would happen after production of the prompt

# it could serialize as

```python
def generate_approaches_to_eamil_somone(linkedinprofile, aboutme):
    """ You are a helpful assistant that generates approaches to email someone based on their linkedin profile and your about me. """

    return f"Come up with one for: {linkedinprofile} given that I am {aboutme}"

@ell2a.simple(model="gpt-4o")
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

@ell2a.simple(model="o1-preview")
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

In fact prompt templates dont really exist within ell2a and this a major flaw in some sense.

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

in ell2a we could theoretically infer those things

```python
def prompt(params : str):
    """Your a good guy"""  # system

    return f"Be a good guy " #User prompt
```

What is the params in this case (params : str)
well actually its their manifestation in the return cause we can have arbitrary args. So it's like we need the DSP abstractions to construct shit. We could do like

But DSP is fundamentally higher level.

Dynamic prompt construciton in ell2a is also limited.

```python
@ell2a.simple()
def hello_with_kshot(name : str, examples : List[str]):
    return [
        ell2a.system("You are a helpful assistant"),
        *examples,
        ell2a.user(f"Say hello to {name}")
    ]

```

but if i wanted to mutate the prompt after creation i would have to do it manually.

so leads us to a prompt api

```python
@ell2a.simple() :
    (lmp : Callable) ->

class LMP(ell2a.Module):
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

what would it look like also how should we do cot in ell2a

```python
def res(question : str) -> str:
    thoughts = think(question)
    answer = thoughts.split("Answer:")[1]
    return answer

@ell2a.simple()
def chain_of_thought(question : str) -> str:
    return f"Reasoning: Let's think step by step in order to {question}. "

```

but if we rewrote dspy and forgot about @ell2a.simple because LMPs are just fucking like weights lol okay so

chain_of_thought =====  W^T (process_into_vector(x))

but like W^T is like a bunch of format strings and arbitrary instructions so then what the fuck is optimizing CoT cause in Ell2a we've basically merged data parsing and instruction formattging into one big ass thring

nah this is bad.

## Meta Prompting

Okay so if prompting is manually setting the W^T of a matrix then we can think of meta prompting as creating programs that generate W (This is what DSPy is doing.) Maybe DSPy (with some modifications) is the right way to go cause it is basically doing.

Let's consider CoT

```python

# Goal: Add "Let's think step by step in order to" to the beginning of the prompt


@ell2a.simple(model="gpt-4o")
def w_0(my_input : str, my_second_input : str) -> str:
    """You are a helpful assistant"""

    return "Please make a poem about " + my_input + " and " + my_second_input

# How do we go from w_0 to a CoT prompt? That's not really the point of DSPy. It's that we should meta prompt this.

def cot(goal : str, n_steps : int, step_prefix : str) -> str:
    return [
        ell2a.user(f"""Reasoning: Let's think step by step in order to {goal}.""")
    ]

@ell2a.simple(model="gpt-4o")
def w_0_my_input_modifier(x : str) -> str:
    """You are a good assistant"""

    return cot(
        goal="Make a poem about " + x,
        n_steps=3,
        step_prefix="Reasoning: "
    )

#  why is this bad? this makes sense to me....

# It's bad because if you want to do multistep stuff like:
# Reasoning Step: <title>
# Rationale: <rationale>
# Next Action: <next action>
# We haven't made it easier to do so. Like obviously you can template and build helper functions but multistep CoT or recursive sutff is difficult.

# you could do something like

@ell2a.simple()
def agent_step(x : str, previous_steps : str) -> str:
    return cot_prompt(
        goal="Make a poem about " + x,
        n_steps=3,
        step_prefix="Reasoning: "
    ) + previous_steps

run_agent(agent_step, x="roses are red")

# but that is still really bad. Idk fuck this.
# Actually i dont htink DSPy is even set up for multistep CoT
# Ah it is

# ... PoT.py
    def forward(self, **kwargs):
        input_kwargs = {
            field_name: kwargs[field_name] for field_name in self.input_fields
        }
        code_data = self.code_generate(**input_kwargs)
        parsed_code, error = self.parse_code(code_data)
        # FIXME: Don't try to execute the code if it didn't parse
        code, output, error = self.execute_code(parsed_code)
        hop = 0
        while hop < self.max_iters and error:
            print("Error in code execution")
            input_kwargs.update({"previous_code": code, "error": error})
            code_data = self.code_regenerate(**input_kwargs)
            parsed_code, error = self.parse_code(code_data)
            # FIXME: Don't try to execute the code if it didn't parse
            code, output, error = self.execute_code(parsed_code)
            hop += 1
            if hop == self.max_iters:
                print("Max hops reached. Error persists.")
                return None
        input_kwargs.update({"final_generated_code": code, "code_output": output})
        answer_gen_result = self.generate_answer(**input_kwargs)
        return answer_gen_result

    def _generate_instruction(self, mode):
        mode_inputs = ", ".join(
            [
                f"`{field_name}`"
                for field_name in self._generate_signature(mode).input_fields
            ],
        )
        mode_outputs = f"`{self.output_field_name}`"
        if mode == "generate":
            instr = [
                f"You will be given {mode_inputs} and you will respond with {mode_outputs}.",
                f"Generating executable Python code that programmatically computes the correct {mode_outputs}.",
                f"After you're done with the computation, make sure the last line in your code evaluates to the correct value for {mode_outputs}.",
            ]
        elif mode == "regenerate":
            instr = [
                f"You are given {mode_inputs} due to an error in previous code.",
                "Your task is to correct the error and provide the new `generated_code`.",
            ]
        else:  # mode == 'answer'
            instr = [
                f"Given the final code {mode_inputs}, provide the final {mode_outputs}.",
            ]

        return "\n".join(instr)
    def _generate_signature(self, mode):
        signature_dict = dict(self.input_fields)
        fields_for_mode = {
            "generate": {
                "generated_code": dspy.OutputField(
                    prefix="Code:",
                    desc="python code that answers the question",
                    format=str,
                ),
            },
            "regenerate": {
                "previous_code": dspy.InputField(
                    prefix="Previous Code:",
                    desc="previously-generated python code that errored",
                    format=str,
                ),
                "error": dspy.InputField(
                    prefix="Error:",
                    desc="error message from previously-generated python code",
                ),
                "generated_code": dspy.OutputField(
                    prefix="Code:",
                    desc="python code that answers the question",
                    format=str,
                ),
            },
            "answer": {
                "final_generated_code": dspy.InputField(
                    prefix="Code:",
                    desc="python code that answers the question",
                    format=str,
                ),
                "code_output": dspy.InputField(
                    prefix="Code Output:",
                    desc="output of previously-generated python code",
                ),
                self.output_field_name: self.signature.fields[self.output_field_name],
            },
        }
        signature_dict.update(fields_for_mode[mode])
        return dspy.Signature(signature_dict

        self.code_generate = dspy.ChainOfThought(
            dspy.Signature(
                self._generate_signature("generate").fields,
                self._generate_instruction("generate"),
            ),
        )
        self.code_regenerate = dspy.ChainOfThought(
            dspy.Signature(
                self._generate_signature("regenerate").fields,
                self._generate_instruction("regenerate"),
            ),
        )
        self.generate_answer = dspy.ChainOfThought(
            dspy.Signature(
                self._generate_signature("answer").fields,
                self._generate_instruction("answer"),
# In Ell2a this would be:

# It's still meta programmign lol i can't get ath "updating the inpout fields like it's fucked.
@ell2a.simple(model="gpt-4o")
def code_generate(question :str ) -> str:
    return cot(
        goal="python code that answer the quesiton {question}",
        n_steps=3,
        format=str
    )

@ell2a.simple(model="gpt-4o")
def code_regenerate(previous_code : str, error : str) -> str:
    return cot(
        goal="regenerate the code {previous_code} to fix the error {error}",
        n_steps=3,
        format=str
    )

@ell2a.simple(model="gpt-4o")
def code_answer(final_generated_code : str, code_output : str) -> str:
    return cot(
        goal="given the final code {final_generated_code} and the output {code_output}, provide the answer",
        n_steps=3,
        format=str
    )

@ell2a.function()
def program_of_though(question : str) -> str:
    input_kwargs = {"question": question}
    code_data = code_generate(**input_kwargs)
    parsed_code, error = parse_code(code_data)
    code, output, error = execute_code(parsed_code)
    hop = 0
    max_iters = 3  # You can adjust this value as needed
    while hop < max_iters and error:
        print("Error in code execution")
        input_kwargs.update({"previous_code": code, "error": error})
        code_data = code_regenerate(**input_kwargs)
        parsed_code, error = parse_code(code_data)
        code, output, error = execute_code(parsed_code)
        hop += 1
        if hop == max_iters:
            print("Max hops reached. Error persists.")
            return None
    input_kwargs.update({"final_generated_code": code, "code_output": output})
    answer_gen_result = code_answer(**input_kwargs)
    return answer_gen_result



program_of_though("roses are red")

# So I don't think we really are getting the
```

Well its clear that ell2a.function is a useful abstraciton so long as the return type is a trackable or serializable type. Perhaps that's not even necessary, but for reconstructing computation graphs it would be

```python

# This is what is really going on, but there can be many adapters in dspy
cot = ChainOfThought(signature, activated=True)

#
adapter = ChatAdapter()
messages = adapter.format(signature, demos, inputs)


# Define the messages (from the Deactivated CoT example)
[
    {
        "role": "system",
        "content": (
            "Your input fields are:\n"
            "1. `question` (str): \n"
            "Your output fields are:\n"
            "1. `rationale` (str): \n"
            "2. `answer` (str): \n\n"
            "All interactions will be structured in the following way, with the appropriate values filled in.\n"
            "[[[[ #### question #### ]]]]\n{question}\n\n"
            "[[[[ #### rationale #### ]]]]\n{rationale}\n\n"
            "[[[[ #### answer #### ]]]]\n{answer}\n\n"
            "[[[[ #### completed #### ]]]]\n\n"
            "You will receive some input fields in each interaction. Respond only with the corresponding output fields, starting with the field `rationale`, then `answer`, and then ending with the marker for `completed`.\n\n"
            "In adhering to this structure, your objective is: \n"
            "Your objective is to provide detailed reasoning (rationale) followed by the final answer."
        )
    },
    {
        "role": "user",
        "content": (
            "[[[[ #### question #### ]]]]\n"
            "What is the capital of France?"
        )
    },
    {
        "role": "assistant",
        "content": (
            "[[[[ #### rationale #### ]]]]\n"
            "To determine the capital of France, we recall that France is a country in Europe, and its most populous city is Paris, which serves as the capital.\n\n"
            "[[[[ #### answer #### ]]]]\n"
            "Paris.\n\n"
            "[[[[ #### completed #### ]]]]\n"
        )
    },
    {
        "role": "user",
        "content": (
            "[[[[ #### question #### ]]]]\n"
            "Who wrote '1984'?"
        )
    },
    {
        "role": "assistant",
        "content": (
            "[[[[ #### rationale #### ]]]]\n"
            "To identify the author of '1984', we consider famous dystopian novelists and recognize that George Orwell is renowned for this work.\n\n"
            "[[[[ #### answer #### ]]]]\n"
            "George Orwell.\n\n"
            "[[[[ #### completed #### ]]]]\n"
        )
    },
    {
        "role": "user",
        "content": (
            "[[[[ #### question #### ]]]]\n"
            "What is the largest planet in our solar system?"
        )
    }
]

```

Okay so let's now revisit meta prompting for a bit:

In ell2a we build a good framework for engineering specific `W = [0, 1, 2, ...]`. In DSPy we have a framework for doing things like `W = th.zeros((a,b))` `y= W^Tx`.

So its like dynamic, but oppinionated prompt construction. How might this look. lets consider the idea that we start at `W = [0, 1, 2, ...]` and then we write `y =W^Tx`; that is we provide starting points for this optimization.
This is less descirptive than DSPy.

```python
@ell2a.simple(model="gpt-4o")
def my_arbitrary_prompt(question :str, context : List[str]) -> str:
    return f"""
    You are a helpful assistant answer the following question about a given context. Do not use any other information.
    Question: {question}
    Context: {context}
    """
```

How do we dynamically optimzie this?

```python
>>> my_arbitrary_prompt(question="What is the capital of France?", context=["France is a country in Europe.", "Paris is the capital of France."])
 [ell2a.user("""You are a helpful assistant.
    Question: What is the capital of France?
    Context: France is a country in Europe. Paris is the capital of France.
    Do the following:
    <..your response>""")]


>>> optimizer = ell2a.BootstrapFewShotOptimizer(top_k=10)
>>> x = [
    dict(
        question="What is the largest planet in our solar system?",
        context=["Jupiter is the largest planet in our solar system.", "Saturn is the second-largest planet."],
    ),
    dict(
        question="Who painted the Mona Lisa?",
        context=["Leonardo da Vinci was an Italian Renaissance polymath.", "The Mona Lisa is a famous Renaissance painting."],
    ),
    dict(
        question="What is the chemical symbol for gold?",
        context=["Gold is a precious metal.", "The periodic table lists elements and their symbols."],
    ),
]
>>> y = [
    "Jupiter",
    "Leonardo da Vinci",
    "Au"
]

>>> better_arbitrary_prompt = optimizer.fit(my_arbitrary_prompt, x=x, y=y)

>>> better_arbitrary_prompt(question="What is the capital of France?", context=["France is a country in Europe.", "Paris is the capital of France."])
[
    # EXAMPLES:
    ell2a.user(
    """
    You are a helpful assistant.
    Question: What is the largest planet in our solar system?
    Context: Jupiter is the largest planet in our solar system. Saturn is the second-largest planet.
    Do the following:
    <..your response>
    """
    ),
    ell2a.assistant(
        """
        Jupiter
        """
    ),
    ell2a.user(
    """You are a helpful assistant.
    Question: Who painted the Mona Lisa?
    Context: Leonardo da Vinci was an Italian Renaissance polymath. The Mona Lisa is a famous Renaissance painting.
    Do the following:
    <..your response>
    """
    ),
    ell2a.assistant(
        """
        Leonardo da Vinci
        """
    ),
    ell2a.user(
    """You are a helpful assistant.
    Question: What is the chemical symbol for gold?
    Context: Gold is a precious metal. The periodic table lists elements and their symbols.
    Do the following:
    <..your response>
    """
    ),
    ell2a.assistant(
        """
        Au
        """
    ),
    # Final user prompt.
    ell2a.user(
        """
        You are a helpful assistant.
        Question: What is the capital of France?
        Context: France is a country in Europe. Paris is the capital of France.
        Do the following:
        <..your response>
        """
    )
]
```

The problem with this mechanism is that it will duplicate bad prompting in the examples rather than being a generic metaprompt that can be reused.

This leads us to an idea

> Prompt optimizers are independent of meta prompts.

DSPy is a DSL for prompting basically lol you define shit in maybe a "BAML" type way and then you can do optimizations much more easily be for you realize a prompt.

You could sovle the problem of going from a specific `W` to a generic `th.randn(W.shape)` and then you could do DSPy on that shit. You would be inferring signatures. Also no problem just copying the DSPy functional API...

Consider:

```python
import dspy

context = ["Roses are red.", "Violets are blue"]
question = "What color are roses?"

@dspy.cot
def generate_answer(self, context: list[str], question) -> str:
    """Answer questions with short factoid answers."""
    pass
```

So they are able to specify a signature and then mutate it from here.  Another example:

```python
@dspy.predictor
def generate_answer(self, context: list[str], question) -> str:
    """Answer questions with short factoid answers."""
    pass
```

The output key is the name of the function...

```
    sig = inspect.signature(func)
    annotations = typing.get_type_hints(func, include_extras=True)
    output_key = func.__name__
    instructions = func.__doc__
    fields = {}
```

Inherently this isn't as expressive as their module class though. I am also unsure about oppinionating pro,pt consturciton, though I suppose you can optimize adapters in a way you wouldn't be able to do with ell2a

```python
# This is pytorch:
# W = th.randn(10, 10)
meta = ell2a.meta(
    instructions="do this",
    inputs={
        x : str,
        y : str
    },
    outputs={
        z : str
    }
)

final = meta.compile()
# But then we have to go to the dsp shit because we want prompts to call other prompts and interact hierarchically like dsp.
# But this creates such an obfuscated view of prompt construction you don't know how the fuck this is happenign udner the hood.
# It's much heasier to udnerstand th.randn(10,10)
# than meta.compile(myadapte)
```

```python
# I am an ML researcher I don't understand how prompting works lol I know how mdoels works and I want to make a model that solves my problem
# In ML we have inptus and outputs hur dur


@ell2a.simple(model="gpt-4o")
def please_solve_my_problem(x : str) -> str:
    return f"Please solve my problem: {x}"

(ell2a.metaprompt(
    instructions="do this",
    inputs={
        x : str,
        y : str
    },
    outputs={
        z : str
    }
))
```

This SHIT FEELS LIKE LANGCHAIN what the FUCK.

There are no rules we don't need parity, but waht about CoT and shit. i mean CoT is a meta prompt. the a variety of inptus and outputs, but i dont see why you can't just do it in ell2a with a cot function

```python


@ell2a.simple(model="gpt-4o")
def write_me_a_blog_post(topic : str) -> str:
    return cot_prompt(
        goal="write a blog post about " + topic,
        step_prefix="Reasoning: "
    )

# this doesnt do the parsing which is hte big problem and htats what cot is..
```python


# ell2a/primitives/cot.py
class CoT(BaseModel):
    reasoning : List[str]
    answer : str

with ell2a.context():
    pass

# this forces the user to wrap their call of this in an @ell2a.function or ell2a.simple, or ell2a.complex etc.
# Or we can ommit this and just let them call it directly in which case we dont need the extra context. You can't just use CoT alone?
@ell2a.function(require_ell2a_context=True)
def cot(instructions : str,  model : str,  **params) -> CoT:
    output = ell2a.simple(
        messages=[
            ell2a.system(f"""
            You are a helpful assistant.
            You must solve a problem using reasoning.
            Your output format should be:
            '''Rationale: Let's think step by step. <reasoning>
            Answer: <answer>'''
            """),
            ell2a.user(instructions),
        ]
        model=model,
        **params
    )
    assert "Rationale:" in output and "Answer:" in output, "Output does not contain Rationale: or Answer:"
    return CoT(
        reasoning=output.split("Answer:")[0].split("Rationale:")[1],
        answer=output.split("Answer:")[1]
    )

# some user shit

@ell2a.function()
def write_a_blog_post(problem : str) -> str:
    result = ell2a.cot(
        model="gpt-4o",
        instructions="solve the following math problem: " + solve_math_problem,
        step_prefix="Reasoning: "
    )
    return result.answer # str

```

So now that we have a CoT implementation, we can imagine a meta prompting framework that constructs an ell2a.function automatically; this is a generic one-shot prompt that can be reused and it's format strings itself can be optimized a la MiPRo etc.

```python
@ell2a.function()
def cot(instructions : str,  model : str,  **params) -> CoT:
    output = ell2a.simple(
        messages=parameterized_prompt(
            input(
                instructions = Field(str, description="The instructions for the prompt")
            ),
            output(
                rationale= Field(str, description="The rationale for the answer"),
                answer= Field(str, description="The answer to the prompt")
            ),
            task="Think step by step and provide the answer",
        )
        model=model,
        **params
    )
    assert "Rationale:" in output and "Answer:" in output, "Output does not contain Rationale: or Answer:"
    return CoT(
        reasoning=output.split("Answer:")[0].split("Rationale:")[1],
        answer=output.split("Answer:")[1]
    )
```

This is back to that bullshit soft prompt idea god damnit which is just signatures. mother fucker
and why do i even need your dogshit function shit anyway.
 Fuck me.
 I hate this.
 Ew
 Ew
  EEWWW

The whole reason for prameterizing the prompt is also getting structured outputs, but this is really overfit to the no structured output case.
Also output doesnt need to be parsed in this case So it would have to look like

```python
class Input(BaseModel):
    instructions : str

class Output():
    rationale : str
    answer : str

output = parameterized_lmp(
    input={
        "instructions" : int = Field(..., description="The instructions for the prompt")
    }
    output={
        "rationale" : str,
        "answer" : str
    },
    task="Think step by step and provide the answer",
)
```

Should we not be able to infer all of this from the actual LMP itself. But I guess in DSPy, you dont have to start with your prompt.

Can't we use the AST to determine all of the variables going into a call to then infer the signature of the prompt?

So like

ell2a.simple(model="gpt-4o", messages=[...])

Track messages back in the AST for this call then find all the format vars. Well what if it's a prompt, then there's nothign we can do. With aprameterized promtps you can not prompt at all.

Don't want to prompt? Try meta prompting.

Specify your inputs and outputs and what you want the model to do. Ell2a will figure out the prompt for you.
There's no real problem with DSPy to this extent except its so obfuscated as to what's going on if you don't understand it you're fucked.

If we can disambiguate reposne formats and all this then maybe this is fine.

I guess if our library looks cleaner than DSPy ultimately with the same functionaltiy internally we are okay.

Meta prompting =
construction of @ell2a.simple call + parsing dynamically from input outputs and instructions.

I think this is the conclusion.

Take the best of DSPy and clean it up.

```python
class Input(BaseModel):
    instructions : Field(str, description="The instructions for the prompt")

class Output(BaseModel):
    answer : Field(str, description="The answer to the prompt")

meta_prompt = ell2a.meta(
    name="blog_post",
    input={
        "instructions" : Field(str, description="The instructions for the prompt")
    },
    output={
        "answer" : Field(str, description="The answer to the prompt")
    },
    instructions="write a blog post about the following topic",
) -> str

```

 Meta prompts are signatures.

Why DSPy requires compilation is that we can have mta promtps call one another but we shouldnt have  to compile before calling because the computatio ngraph is not known until runtime.

I think the prolem with all this is that when i do th.randn(10,10) i can immediately use it i can imemdiately use the layer it might be garbage but i can. SO if I were to take this in ell2a I can imagine.

```python
meta_prompt = ell2a.lmp(
    name = "blog_post",
    input={
        "instructions" : Field(str, description="The instructions for the prompt")
    },
    output={
        "answer" : Field(str, description="The answer to the prompt")
    },
    instructions="write a blog post about the following topic",
)
```

then I can just call meta_prompt() # and it will give me the prompt. the signature is the parameter but we can have different "initializations" instead of jsut LMP
compiling is uneccessary because we can access the parameterixaiton at runtime to optimize. This also allows the user to see what hhe fuck the thing is doing.

```python

ell2a.meta.io_lmp(
    ell2a.signature(
        Input(instructions : str),
        Output(answer : str),
    instructions="write a blog post about the following topic",
    ),
    model="gpt-4o",
)

cot_blog = ell2a.meta.cot_lmp(
    ell2a.signature(
        Input(instructions : str),
        Output(title : str, content : str),
        instructions="write a blog post about the following topic",
    ),
    model="gpt-4o",
)


@ell2a.function()
def write_blog_post(instructions : str) -> str:
    blog = cot_blog(instructions)
    return f"# {blog.title}\n\n{blog.content}"
```

Now let's say we want to optimize write_blog_post.

```python
x = [
    "AI",
]
y = [
    BlogPost(title="AI", content="AI is the future."),
]


optimized_blog_post = ell2a.FewShotOptimizer().fit(write_blog_post, x=x, y=y)
```

so because this is functional is cot_blog now changed? this the reason for modules in dspy because if i want to see the updated params is it cot_blog?
 NO so we need to specify it as learnable:

```python
filters = ell2a.parameterized(ell2a.cot(
    model="gpt-4o",
    instructions="write a blog post about the following topic",
    signature=ell2a.signature(
        Input(instructions : str),
        Output(title : str, content : str),
    ),
 ))
```

 so we are going full functional now?

 we could do shit like this

```python
 @ell2a.simple(model="gpt-4o")
 def my_intial_prompt(instructions : str) -> str:
    return f"write a blog post about the following topic: {instructions}"


 >>> ell2a.FewShotOptimizer().fit(my_intial_prompt, x=x, y=y)
 exception: NotLearnableError("my_intial_prompt is not learnable")

 learnable = ell2a.learnable(my_intial_prompt)
 final_prompt =ell2a.FewShotOptimizer().fit(learnable, x=x, y=y)
 >>> final_prompt("AI")
 "write a blog post about the following topic: AI"

 learnable.data # This is the final prompt

 ```

 ```python


import torch as th


weights = th.nn.Parameter(th.randn(10))


def forward(x):
    return x * weights


x = th.randn(10)

print(forward(x))
print(weights)

# OOOH WAHT IF WE DID MANY TYPES OF LEARNABLES in
```

like:

```python
@ell2a.simple(model="gpt-4o")
def my_initial_prompt(instructions : str) -> str:
    return f"{ell2a.learnable("You must write a blog post about the following topic:")} {instructions}"

```

Then we can optimize the strings!
I dont think "few shot" is an optimizer though. I guess you could say if you want to do few shot, y9ou would make the whole prompt learnable

```python
learnable_prompt = th.learnable(my_initial_prompt)


ell2a.FewShotOptimizer().fit(learnable_prompt, x=x, y=y)

-->

def final_prompt(instructions : str) -> str:
    return [
        ell2a.system("You are a helpful assistant."),
        ell2a.user(x[0]),
        ell2a.assistant(x[1]),
        ...
        ell2a.user("You must write a blog post about the following topic:")
        ell2a.user(instructions)
    ]
```

but how do we serialize this? do we mutate the code?  no. we just have it serialized like this

```python
def my_initial_prompt(instructions : str) -> str:
    return f"{ell2a.learnable("You must write a blog post about the following topic:")} {instructions}"

my_intial_prompt_optimized=  fewhsot(my_intial_prompt, x=x, y=y)


ell2a.simple(model="gpt-4o", messages=learnable_prompt.data)

```

ew no. I guess I thought it was cool to have strings be parameters. in arbitrary ways.
