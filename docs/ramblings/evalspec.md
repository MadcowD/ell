
```python

# Example implementation based on the ideas discussed

from typing import List, Dict, Any, Union, Callable
import inspect
import numpy as np

# Define a flexible Dataset type
Dataset = List[Dict[str, Any]]

# Example dataset
dataset: Dataset = [
    {"input": "What is the capital of France?", "expected_output": "Paris", "difficulty": "easy"},
    {"input": "What is the square root of 144?", "expected_output": "12", "difficulty": "medium"},
    # ... more data points
]

# Example LMP (Language Model Program)
def my_lmp(input: str) -> str:
    # This is a mock LMP that just returns the input
    return input

# Example score functions
def accuracy_score(expected_output: str, output: str) -> float:
    return float(expected_output.lower() == output.lower())

def difficulty_weighted_score(difficulty: str, expected_output: str, output: str) -> float:
    base_score = float(expected_output.lower() == output.lower())
    difficulty_weight = {"easy": 1.0, "medium": 1.5, "hard": 2.0}
    return base_score * difficulty_weight.get(difficulty, 1.0)

class Evaluation:
    def __init__(self, name: str, dataset: Dataset, lmp: Callable, scores: List[Callable]):
        self.name = name
        self.dataset = dataset
        self.lmp = lmp
        self.scores = scores

    def run(self) -> Dict[str, List[float]]:
        results = {score.__name__: [] for score in self.scores}
        
        for datapoint in self.dataset:
            # Run the LMP
            lmp_input = datapoint.get("input")
            if isinstance(lmp_input, str):
                output = self.lmp(lmp_input)
            elif isinstance(lmp_input, dict):
                output = self.lmp(**lmp_input)
            elif isinstance(lmp_input, list):
                output = self.lmp(*lmp_input)
            else:
                raise ValueError(f"Unsupported input type: {type(lmp_input)}")
```
Alright, so this part is a bit too magical. Essentially, what it's doing is taking the input object and, if it's a single object, passing it directly into the LMP. Otherwise, it destructures the arguments. I do appreciate the use of **kwargs versus list destructuring; it's quite elegant. We can think of it as handling both args and kwargs, which is fine. However, it's also quite clean to write your dataset as single input elements.

```python
            # Calculate scores
            for score in self.scores:
                args = inspect.signature(score).parameters
                datapoint_subset = {k: datapoint.get(k) for k in args if k != 'output'}
                score_output = score(**datapoint_subset, output=output)
                results[score.__name__].append(score_output)

        return results

# Usage example
eval = Evaluation(
    name="my_evaluation",
    dataset=dataset,
    lmp=my_lmp,
    scores=[accuracy_score, difficulty_weighted_score]
)

results = eval.run()
print(results)

# You could then add methods to analyze and visualize the results
# For example:
def analyze_results(results: Dict[str, List[float]]):
    for score_name, scores in results.items():
        print(f"{score_name}:")
        print(f"  Mean: {np.mean(scores):.4f}")
        print(f"  Median: {np.median(scores):.4f}")
        print(f"  Min: {np.min(scores):.4f}")
        print(f"  Max: {np.max(scores):.4f}")

analyze_results(results)

```

So now let's consider The usability of these input shapes. If we're really going to accept that, there's like some special input data point arg.


```python
class DatapointPD(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    input : Dict[str, Any] | List[Any]
    labels: Dict[str, Any]


# or

class DatapointTD(TypedDict, total=False):
    input : Dict[str, Any] | List[Any]

# finally
Dataset = List[Datapoint]


# This is actually quite in the style of ell where we have input and output in ell studio as either a list of arguments or a dictionary of kwargs.
dataset = [
    Datapoint(input=["What is the capital of France?"], labels={"expected_output": "Paris"}),
]

# or
dataset = [
    {"input" : {'question' : "What is the capital of France?"}, "answer" : "Paris"},
]
#/equivalently
dataset = [
    DatapointTD(input=["What is the capital of France?"], labels={"expected_output": "Paris"}),
]

```

This approach is quite elegant. We need to use Pydantic models with `total=False` so we can validate that each entry has an input.

Imagine defining a dataset in this structured way, where every entry must at least have the shape of an input. You can then add arbitrary fields to the dataset columns. This avoids the issue where the shape of the LMP function needs to be transformed.

So let's actually write out what the final form of this might actually look like and see if it's palatable. If it's not that's okay.
```python


@ell.simple(model="gpt-4o-mini")
def write_a_poem(about :str):
    """You are PoetGPT.  You always write in iambic pentameter. Only answer with a poem."""
    return f"Write a poem about {about}"


@ell.simple(model="gpt-4o-mini")
def iambic_pentameter(poem :str):
    return f"Is the following poem in iambic pentameter? {output} answer with yes or no."


# This is like OpenAI + weave evals.

eval = Evaluation(
    name="poem-eval",
    dataset=[
        Datapoint(input=["a rose"], must_contain="rose", minimum_length=100),
        Datapoint(input=["a sunset"], must_contain="sunset", minimum_length=100),
        Datapoint(input=["a rainbow"], must_contain="", refuse=True, minimum_length=100),
    ],
    criterion=[
        lambda datapoint, output: datapoint.must_contain in output,
        lambda datapoint, output: len(output) >= datapoint.minimum_length,
        lambda datapoint, output: "I refuse to write a poem about that" in output or not datapoint.refuse,
        lambda datapoint, output: "yes" in iambic_pentameter(output).lower(),
    ]
)


eval.run(write_a_poem)
# a set of scores.
# Then we modify write a poem



@ell.simple(model="gpt-4o-mini")
def write_a_poem(about :str):
    """You are PoetGPT.  You always write in iambic pentameter. Only answer with a poem. Say I refuse to write a poem about that if you are asked to write about rianbows """
    return f"Write a poem about {about}"


# Now the refusal criterion will work.
eval.run(write_a_poem)

# Now we improve iambic pentameter score by trying to rewrite the poem.

@ell.simple(model="gpt-4o-mini")
def better_poem_writer(about :str):
    """You are a poet. You are a poet who is extremely good at writing iambic pentameter. If the poem says I refuse just copy the refusal"""
    initial_poem = write_a_poem(about)

    return f"Rewrite the following poem in iambic pentameter: {initial_poem}"


eval.run(better_poem_writer)
# highest score.

```

I think I like this Eval the most from any of the specs I have come up with. You can just throw accuracy criteria in there. It's very easy by specifying how the dataset looks. The Weave guys definitely built a really good abstraction here. Some small changes around where things feel magical make this pretty close to an abstraction that we can use. In the above example, it's extremely readable as to what's going on, and I can imagine a very simple flow where I iteratively improve things. I don't have to worry about what's going on with the individual args or kwargs, as they're specified in the input dict. If there's a mismatch, then I just use arguments instead of kwargs. As for the criterion, you just take in the data point and the output. It's just two positional arguments. The data point is literally just what came from the dataset. So if you ever need to look at the schema, it's all there. Inputs are separated out. Inputs are a requirement for data points. We can validate that when we build the eval. This is a very particular type of dataset, and this lets you very quickly and rapidly develop fast evaluations.

The only problem here is I think what is very nice about the OpenAI evaluation product is that it comes with tons of evaluations by default. For example, text similarity, text quality, BLEU score, things like this. And because the dataset is so free, we don't have an expected output. We can't run metrics automatically.

We could, by default, actually include something inside the metric functionality, like a special keyword in the dataset. If we actually use the reserved expected output keyword, then you can just use pre-canned metrics without having to specify them, because then we're sort of moving the transmutation of metrics to the criterion specification, right? But I could automatically run things like BLEU score or text similarity if you use the expected output keyword. Otherwise, I guess we could just make them instantiable, so I might actually prefer this. So let's just do this, for example.


```python


from ell.evals import cosine_similarity

@ell.simple(model="gpt-4o-mini")
def write_a_poem(about :str):
    """You are PoetGPT. Write with cheesy well-known poems if available."""
    return f"Write a poem about {about}"


eval = Evaluation(
    name="poem-eval",
    dataset=[
        # jsonl injection into dataset formula
        Datapoint(input=["a rose"], expert_poem="Roses are red, violets are blue, sugar is sweet, and so are you.")
    ],
    criterion=[
        cosine_similarity("text-embedding-3-small", expected_output="expert_poem", inner_product="normal")
    ]
)

# can automatically do cosine similarity & other nice things
eval.run(write_a_poem)

```


