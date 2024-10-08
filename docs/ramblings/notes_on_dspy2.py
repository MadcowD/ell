from typing import List
import ell


def chain_of_thought(input : str, instruction : str):
    @ell.simple(model='gpt-4o')
    def chain(input : str):
        return ell.user(input=input, instruction=instruction)
    return chain


ell.init(verbose=True, store='./logdir')


def nn_layer(params, x):
    return params.dot(x)


class Model:
    def __init__(self, layers = 10):
        self.layer_weights = [np.randn(10, 10) for _ in range(layers)]

    def save(self):
        pass

    def __call__(self, x):
        return dspy.variable("You arew a good llm that does ")  + x

        for weight in self.layer_weights:
            x = x * weight
        return x


# People really want this?
expand_example = predict(
    input={}
    instruction=."
)

number_to_classify = predict(
    input="example",
    instruction="Infer the number of companies you need to classify between. Return an integer between 1-5 based on the given example."
)

TGCIDs = predict(
    input=["context", "example", "n"],
    instruction="Create a list of viable TGCIDs. TGCIDs should be a comma-separated list of TCGIDs of length n. The TGCIDs should be relevant to the given context and example."
)

@ell.function()
def generate_answer(self, example : str, k : int):
    company_descriptions = expand_example(example)
    n = number_to_classidfy(example)
    passage="asd"
    return TGCIDs()



soft_generate_answer = sft(generate_answer)

objective_function = lambda: y_pred, x   jaracard(y_pred, soft_generate_answer(x))



for _ in range(100):
    loss = objective_function(x,y)
    loss.backward()
    optimizer.step()





# Ver yeasy to try new configurations
    
if __name__ == "__main__":
    generate_answer("A tech giant known for its search engine and various internet services.")



# Reasonable plan

# 1. Simple deifned prompts
# 2. Combination of prompts
# 3. Evals
# 4. MLE tyring to prompt.

# Underneath.
@dataclass
class Closure:
    model : Any
    prompt : str

@dataclass
class LMP:
    closure : Closure
    prompt_fn : Callable[[Any], Union[str, List[Message]]]


    def __call__(self, x):
        prompt = self.prompt_fn(x)
        # complex stuff

# Borrow DSPy

# A compatible model based interface for LMPs
class ChainOfThought(ell.LMP):
    def __init__(self, input_shape, output_shape, instruction : str):
        
    def prompt(self, input):
        return [
            ell.system("You are a helpful assistant. Who solves the following task: " + self.instruction),

        ]
    
    def parse(self, output):
        # Post process of output.
        return output


# Automatic cration of LMPs from decorators:

@ell.simple(model="gpt-4o")
def say_hello(name : str):
    return f"Say hello to {name}!"

# ->
# This inherently gets created underneath.
class SayHello(ell.LMP):
    def __init__(self, input_shape, output_shape):
        super().__init__(input_shape, output_shape)

    def prompt(self, input):
        return [
            ell.user(f"Say hello to {input}!")
        ]
        
    def parse(self, output):
        return output.text







