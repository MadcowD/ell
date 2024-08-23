from typing import List
from pydantic import BaseModel, Field
import ell
from ell.types import Message

ell.config.verbose = True


@ell.tool()
def create_claim_draft(claim_details: str, claim_type: str, claim_amount: float, 
                       claim_date : str = Field(description="The date of the claim in the format YYYY-MM-DD.")):
    """Create a claim draft. Returns the claim id created."""
    return "claim_id-123234"

@ell.tool()
def approve_claim(claim_id : str):
    """Approve a claim"""
    pass

@ell.complex(model="gpt-4o", tools=[create_claim_draft, approve_claim], temperature=0.1)
def insurance_claim_chatbot(message_history: List[Message]):
    return [
        ell.system( """You are a an insurance adjuster AI. You are given a dialogue with a user and have access to various tools to effectuate the insurance claim adjustment process. Ask question until you have enough information to create a claim draft. Then ask for approval."""),
    ] + message_history


if __name__ == "__main__":
    from ell.stores.sql import SQLiteStore
    ell.set_store(SQLiteStore('sqlite_example'), autocommit=True)
    ell.config.verbose = True

    done = False
    message_history = []
    while True:
        user_message = input("User: ")
        if user_message == "exit":
            break
        message_history.append(ell.user(user_message))
        response = insurance_claim_chatbot(message_history)
        
        print("\033[92m" + response.role + ": " + response.content[0].text + "\033[0m")
        # if tool calls print that
        if response.content[0].tool_calls:
            print("Tool call made")
        message_history.append(response)
        

