from typing import Optional


@ell.simple(model="gpt-4o")
def write_a_poem(about : str) -> str:
    """You are poem GPT"""
    return f"Write a poem about {about}"


class ClarityFeedback(ell.Feedback):
    """Please provide feedback on the poem's clarity."""

    score : float = Field(..., gt=0, lt=10, description="The clarity of the poem on a scale of 1 to 10")
    why : Optional[str] = Field(..., description="Any additional feedback you want to provide")


class OnTopicFeedback(ell.Feedback):
    """Your goal is to assess whether the poem is on topic."""

    was_relevant : bool = Field(..., description="Was the poem relevant to the input")

@ell.complex(model="gpt-4o", response_model=ClarityFeedback)
def model_clarity(datapoint, output):
    return [
        ell.system("You are a helpful assistant that provides feedback on the clarity of a poem."),
        ell.user(f"Based on the following input: {datapoint['input']} evaluate the following output: {output}"),
    ]



ell.human_feedback(

eval = Evaluation(
    name="eval",
    dataset=[
        {"input": "roses"},
        {"input": "violets"},
        {"input": "sunflowers"},
        {"input": "daisies"},
    ],
    metric={
        "clarity": ell.human_feedback(ClarityFeedback),
        "relevance": ell.human_feedback(OnTopicFeedback),
        "model_clarity": model_clarity,
    }
)


eval.run(write_a_poem, dataset=["roses", "violets", "sunflowers", "daisies"])