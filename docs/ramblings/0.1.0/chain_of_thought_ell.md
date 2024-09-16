
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


## Meta Prompting

Okay so if prompting is manually setting the W^T of a matrix then we can think of meta prompting as creating programs that generate W (This is what DSPy is doing.) Maybe DSPy (with some modifications) is the right way to go cause it is basically doing. 

Let's consider CoT

```python

# Goal: Add "Let's think step by step in order to" to the beginning of the prompt


@ell.simple(model="gpt-4o")
def w_0(my_input : str, my_second_input : str) -> str:
    """You are a helpful assistant"""

    return "Please make a poem about " + my_input + " and " + my_second_input

# How do we go from w_0 to a CoT prompt? That's not really the point of DSPy. It's that we should meta prompt this.

def cot(goal : str, n_steps : int, step_prefix : str) -> str:
    return [
        ell.user(f"""Reasoning: Let's think step by step in order to {goal}.""")
    ]

@ell.simple(model="gpt-4o")
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

@ell.simple()
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
# In Ell this would be:

# It's still meta programmign lol i can't get ath "updating the inpout fields like it's fucked.
@ell.simple(model="gpt-4o")
def code_generate(question :str ) -> str:
    return cot(
        goal="python code that answer the quesiton {question}",
        n_steps=3,
        format=str
    )

@ell.simple(model="gpt-4o")
def code_regenerate(previous_code : str, error : str) -> str:
    return cot(
        goal="regenerate the code {previous_code} to fix the error {error}",
        n_steps=3,
        format=str
    )

@ell.simple(model="gpt-4o")
def code_answer(final_generated_code : str, code_output : str) -> str:
    return cot(
        goal="given the final code {final_generated_code} and the output {code_output}, provide the answer",
        n_steps=3,
        format=str
    )

@ell.function()
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

Well its clear that ell.function is a useful abstraciton so long as the return type is a trackable or serializable type. Perhaps that's not even necessary, but for reconstructing computation graphs it would be


```python

# meta prompting thoughts again. what the fuck is cot. lol this is so stupid.




```