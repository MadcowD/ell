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



