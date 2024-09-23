from typing import List, Optional
import ell
from pydantic import BaseModel, Field



 
class Test(BaseModel):
    name: str = Field(description="The name of the person")
    age: int = Field(description="The age of the person")
    height_precise: float = Field(description="The height of the person in meters")
    is_cool: bool

@ell.complex(model='gpt-4o-2024-08-06', response_format=Test)
def create_test(text: str):
    """You are a test model. You are given a text and you need to return a pydantic object."""
    return "do it!" 


ell.init(verbose=True, store='./logdir')
import json
if __name__ == "__main__":
    result = create_test("ads")
    print(result)


