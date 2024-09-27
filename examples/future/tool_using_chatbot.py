from typing import List
from pydantic import BaseModel, Field
import ell
from ell.types import Message
from ell.stores.sql import SQLiteStore



ell.init(verbose=True, store='./logdir', autocommit=True)


@ell.tool()
def create_claim_draft(claim_details: str, claim_type: str, claim_amount: float, 
                       claim_date : str = Field(description="The date of the claim in the format YYYY-MM-DD.")):
    """Create a claim draft. Returns the claim id created."""
    print("Create claim draft", claim_details, claim_type, claim_amount, claim_date)
    return "claim_id-123234"

@ell.tool()
def approve_claim(claim_id : str):
    """Approve a claim"""
    return "approved"

@ell.complex(model="claude-3-5-sonnet-20240620", tools=[create_claim_draft, approve_claim], temperature=0.1, max_tokens=400)
def insurance_claim_chatbot(message_history: List[Message]) -> List[Message]:
    return [
        ell.system( """You are a an insurance adjuster AI. You are given a dialogue with a user and have access to various tools to effectuate the insurance claim adjustment process. Ask question until you have enough information to create a claim draft. Then ask for approval."""),
    ] + message_history
 


if __name__ == "__main__":
    message_history = []

    # Run through messages automatically!
    user_messages = [
        "Hello, I'm a customer",
        'I broke my car',
        ' smashed by someone else, today, $5k',
        'please file it.'
    ]
    for user_message in user_messages:
        message_history.append(ell.user(user_message))

        message_history.append(response_message := insurance_claim_chatbot(message_history))

        if response_message.tool_calls:
            print("Tool call made")
            next_message = response_message.call_tools_and_collect_as_message()
            print(repr(next_message))
            print(next_message.text)
            message_history.append(next_message)
            insurance_claim_chatbot(message_history)
