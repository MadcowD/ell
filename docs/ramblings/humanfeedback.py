from typing import Optional
from pydantic import BaseModel, Field
from ell import Evaluation
import ell

topic_dataset = [
    {"input": "roses"},
    {"input": "violets"},
    {"input": "sunflowers"},
    {"input": "daisies"},
]

@ell.simple(model="gpt-4o")
def write_a_poem(about : str) -> str:
    """You are poem GPT. Make it 3 sentences long at most."""
    return f"Write a poem about {about}"


class PoemFeedback(BaseModel):
    """Please provide feedback on the poem."""

    clarity: float = Field(..., ge=1, le=10, description="The clarity of the poem on a scale of 1 to 10")

    approve : bool = Field(..., description="If the poem is good enough to be approved")


eval = Evaluation(
    name="eval",
    dataset=topic_dataset,
    labels={
        "human_feedback": ell.human_feedback(PoemFeedback),
        "length": lambda output: len(output)
    }
)
eval.run(write_a_poem)

def Dataset(*args, **kwargs):
    return args[0]

dataset = Dataset([
    {"input": "roses"},
    {"input": "violets"},
    {"input": "sunflowers"},
    {"input": "daisies"},
])


# SFT.

class StructuredPoem(BaseModel):
    poem: str = Field(..., description="The poem", max_length=100)

    @field_validator("poem")
    def poem_length(cls, v):
        if len(v) > 100:
            raise ValueError("Poem must be 100 characters or less")
        # check punctuation
        if not v.endswith("."):
            raise ValueError("Poem must end with a period")
        
        return v
    notes : Optional[str] = Field(None, description="Any additional notes about the poem")

@ell.human(response_format=StructuredPoem)
def write_a_poem(topic):
    """You should write a poem about the topic keep all poems under 100 characters"""
    return f"Write a poem about {topic}"

@ell.human():
def write_a_poem_human(topic):
    """You are a human writing poems"""
    
    expert_poem_str = yield f"Write a poem about {topic}"

    return StructuredPoem(
        poem=expert_poem_str,
        notes= yield "Please provide feedback on the poem."
    )

# Decide to do the structured poem response format for. Human sft data or something of this form. Then we need to inherently support structured outputs across the entire api in a meaningful way The yield format is quite interesting because it allows us to reconstitute the format of. sort of a dialog between the labeler and Data that is presented and present arbitrary data at any point in time during the human labeling process or human sft data generation process. But this also doesn't allow the dynamic generation of uis that are clean and beautiful in some sense. Of course, we could have markdown data and better renderers for raw data contained within, for example, write a poem about topic and things like this. But this isn't a fully. thought out solution. I do like that this is kind of consistent, right? So by using these resumable generators with async or not async, but just standard send. We're able to actually Ask for various different Structured data and reconstituted directly in python in a nice way, so that the final result is this structured poem. Therefore What we sft on is a multi message context, where you. Have it actually output, like the since ultimately we can only sft on strings at any given point in time. There's no magic occurring. And what we sft on is like this conversation thread here. So if this were like a multiple, like I could say, you know, something like The expert poemster is the first yield and then the additional notes or feedback is the 2nd sort of yield. This broader constitution of human feedback is actually kind of interesting

dc = ell.DataCollection(
    dataset=dataset,
    number_examples_per_datapoint=10,
)

dc.run(write_a_poem)






eval = Evaluation(
    name="eval",
    dataset=topic_dataset,
    metrics={
        "human_feedback": ell.human_feedback(PoemFeedback),
        "length": lambda output: len(output)
    }
)
res = eval.run(write_a_poem)

res.scores # dict{
#     "length": [10, 10, 10, 10],
#     "human_feedback": [
#         # or Deferred
#         {
#             "clarity": 8,
#             "approve": True
#         },
#         {
#             "clarity": 8,
#             "approve": True
#         },
#     ]
# }

# we could construct the db model.

# or is human feedback not a metric???
eval = Evaluation(
    name="eval",
    dataset=topic_dataset,
    annotations={
        "length": lambda output: len(output)
        "human_feedback": ell.human_feedback(PoemFeedback),
        "reversed": lambda output: output[::-1]
    },
    criterion=lambda annotations: annotations["human_feedback"].approve and annotations["length"] < 100
)



eval = Evaluation(
    name="eval",
    dataset=topic_dataset,
    scores={ # only callable[..., float]
        "length": lambda output: len(output)
    },
    annotations={ # callable[..., Any] # if its a pydantic type then we pull out the relevant fields?
        "human_feedback": ell.human_feedback(PoemFeedback),
        "reversed": lambda output: output[::-1]
    },
    # final passing criterion optionally but any metric itself could be optimized against.
    criterion=lambda annotations: annotations["human_feedback"].approve and annotations["length"] < 100
)


# multiple criteria doesnt make sense now and so on

# we also have this nice thing
EvaluationRunLabelerResult 
# whic automatically yields the mean of a particular labeler result....
# could be like
x = eval.run(write_a_poem).results["human_feedback"] # whic his a EvaluationRunLabelerResult....
x.mean() # would be None if its a type of string otherwise. no this isn't quite rigjht since we dont get access to the right components 

# criterion is a aggregator funciton over annotations 

# if metric(dp, output) -> float compute summary statistics over the metric.
# otherwise it's just raw data to adorn the final eval with

# then what does the final result object look like
# Does this make like 3 different types of invocaiton labeler or what if they are all annotaitons & we have one criterion flag for a pass rate. What about computing mean metrics? 

# this actually stratifies the problem too much, if I watn to track multiple metrics then I have to make a new table for each metric. 
# in general I want that labels are just simple types with the exception of human feedback. 
# [float, str, bool] as in the DB schema we buiklt

FieldInfo(annotation=bool, default=None, description='If the poem is good enough to be approved')
# its sad because effectively human feedback also matches 
class EvaluationResults(BaseModel):
    outputs: List[Any] = Field(default_factory=list)
    scores: Dict[str, List[float]] = Field(default_factory=dict)
    annotations: Dict[str, List[Any]] = Field(default_factory=dict)
    criterion: List[bool] = Field(default_factory=list)

# A problem here is that criterion is just like a final pass fail, but we might actually want to construct final. Scores that are a function of previous scores and so on. But this is just too much overloading of a feature where someone could implement such. A Functionality via. Inheritance. 


class EvaluationRun(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    # we could get really seperated.
    results: EvaluationResults = Field(default_factory=EvaluationResults)
    dataset : Dataset = Field(default_factory=list)
    lmp: Optional[LMP] = Field(default=None)
    outputs: List[Any] = Field(default_factory=list)
    api_params: Dict[str, Any] = Field(default_factory=dict)
    start_time: datetime = Field(default_factory=datetime.now)
    end_time: Optional[datetime] = None



x = eval.run(write_a_poem)

x.dataset # [{'input': 'roses'}, {'input': 'violets'}, {'input': 'sunflowers'}, {'input': 'daisies'}]
x.outputs # [..., ..., ..., ...] (lmp outptus) 
x.results.scores # {"length": [10, 10, 10, 10]} #always can expect a numpy array
x.results.annotations # {"human_feedback": [..., ..., ..., ...], "reversed": [..., ..., ..., ...]}
x.results.aggregate_annotations() # {"human_feedback": ..., "reversed": ...} maybe???? idk im a little sad about this one
x.results.criterion # [True, True, True, True] 









ell.init(verbose=True)
def render_poem_and_collect_feedback(topic):
    # ASCII art for poem presentation
    print("""
    ╭───────────────────────────────────────────╮
    │             🌸 Poem Feedback 🌸           │
    ╰───────────────────────────────────────────╯
    """)

    # Call write_a_poem function
    poem = write_a_poem(topic)

    # Collect human feedback
    print("""
    ╔══════════════════════════════════════════╗
    ║        🎭 Human Feedback Section 🎭      ║
    ╚══════════════════════════════════════════╝
    """)
    
    feedback_data = {}
    for field_name, field in PoemFeedback.model_fields.items():
        if field.annotation == float:
            while True:
                try:
                    value = float(input(f"    📊 {field.description} ({field.metadata[0].ge}-{field.metadata[1].le}): "))
                    if field.metadata[0].ge <= value <= field.metadata[1].le:
                        feedback_data[field_name] = value
                        break
                    else:
                        print(f"    ⚠️  Please enter a number between {field.metadata[0].ge} and {field.metadata[1].le}.")
                except ValueError:
                    print("    ❌ Please enter a valid number.")
        elif field.annotation == str:
            feedback_data[field_name] = input(f"    💬 {field.description}: ")
        elif field.annotation == bool:
            feedback_data[field_name] = input(f"    ✅/❌ {field.description} (yes/no): ").lower() == 'yes'

    # Create PoemFeedback object
    feedback = PoemFeedback(**feedback_data)

    print("""
    ╔══════════════════════════════════════════╗
    ║        🙏 Thank You for Your Input 🙏     ║
    ╚══════════════════════════════════════════╝
    """)
    return feedback

# Example usage
if __name__ == "__main__":
    for topic in ["roses", "violets", "sunflowers", "daisies"]:
        feedback = render_poem_and_collect_feedback(topic)
        print(f"\nCollected feedback for poem about {topic}:")
        print(feedback)
        print("\n" + "="*50 + "\n")



