from typing import List
import ell
from ell.types import Message
import os
import re
from pydantic import BaseModel

# This is an example of how you can use the ELL API to create a o1(strawberry)-like reasoning agent.
# The main 'trick' basically lies in letting the LLM take multiple turns and reason with itself.
# This is just a simple example, and you can make it more complex by modifying the prompt.

# Notes:
# - I found that xml output works better than json for small models (even gemma:2b can produce reasoning steps with a carefully crafted prompt)
# - Markdown might even work even better (esp gemma:2b is very quirky about the output format, and tends to produce markdown)
# - Its tricky to get the output in the right format, so I used regex to extract the reasoning step. This is not ideal.
# - It's not obvious what problems are better solved with reasoning steps, so you may need to experiment.

# We will use the llama3.1 model for this example.
MODEL = "llama3.1:latest"

ell.config.verbose = True
ell.models.ollama.register("http://127.0.0.1:11434/v1")

SYSTEM = """
You are an expert AI assistant that explains your reasoning step by step.
For each step, provide a title that describes what you're doing in that step, along with the content.
Decide if you need another step or if you're ready to give the final answer.
Respond in xml format with 'title', 'content', and 'next_action' keys.

IMPORTANT GUIDELINES:
- Each reasoning step must include a title, content, and next_action.
- Be aware of your limitations as an LLM and what you can and cannot do.
- Use as many reasoning steps as possible. At least 3.
- Double-check your previous reasoning steps when providing a new step. You may be wrong and need to re-examine.
- In your reasoning, include exploration of alternative answers.
- Fully explore all possibilities before providing the final answer. Always be thorough, and check your reasoning  with an extra step before you give your final answer.
- When you say that you are re-examining, you must actually re-examine, and use another approach to do so. Do not just say you are re-examining.
- The final answer MUST include content with the concluded response to the original user question.
- The only actions available are 'continue' or 'final_answer'
- The next_action key can only be set to 'continue' for all steps except the final step, which must be set to 'final_answer'.
- Only respond with one single step at a time. Do not provide multiple steps in one response.

An example of a valid xml response:
```xml
<reasoning>
    <title>Identifying Key Information</title>
    <content>To begin solving this problem, we need to carefully examine the given information and identify the crucial elements that will guide our solution process. This involves...</content>
    <next_action>continue</next_action>
</reasoning>
```
"""

@ell.simple(model=MODEL, temperature=0.0)
def reasoning_agent(history: List[Message]) -> List[Message]:
    return [SYSTEM] + history

class ReasoningStep(BaseModel):
    title: str
    content: str
    next_action: str

    @staticmethod
    def from_response(response: str):
        reasoning = re.search(r"<reasoning>(.*?)</reas", response, re.DOTALL)
        reasoning = re.search(r"<reasoning>(.*?)</reas", response, re.DOTALL)
        if reasoning:
            reasoning = reasoning.group(1).strip()
            title = re.search(r"<title>(.+)</tit", reasoning, re.DOTALL)
            content = re.search(r'<content>(.+)</cont', reasoning, re.DOTALL)
            next_action = re.search(r'_action>(.+)</next_', reasoning, re.DOTALL)
            if not title or not content or not next_action:
                return None
            return ReasoningStep(title=title.group(1), content=content.group(1), next_action=next_action.group(1))
        return None

def main():
    ell.set_store('./logdir', autocommit=False)

    user_prompt = "Tanya is 28 years older than Marcus. In 6 years, Tanya will be three times as old as Marcus. How old is Tanya now?"
    # user_prompt = input("Prompt: ")
    # if user_prompt == "exit":
    #     break

    assistant_prompt = "Thank you! I will now think step by step following my instructions, starting at the beginning after decomposing the problem"
    history = [ell.user(user_prompt), ell.assistant(assistant_prompt) ]
    # some models don't like the assistant_prompt
    # history = [ell.system(system_prompt), ell.user(user_prompt) ]

    response = reasoning_agent(history)
    step = ReasoningStep.from_response(response)
    if not step:
        print(f"Assistant(raw): {response}")
    else:
        while step:
            response = reasoning_agent(history)
            step = ReasoningStep.from_response(response)
            if not step:
                print(f"Assistant(raw): {response}")
                break
            print(f"{step.next_action}: {step.title}: {step.content}")
            if step.next_action == "final_answer":
                break

            history.append(ell.assistant(response))
            # some models don't require this message, but some just don't work without it, your mileage may vary
            history.append(ell.user("continue"))

if __name__ == "__main__":
    main()
