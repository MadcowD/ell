from typing import List, Optional
import ell
from pydantic import BaseModel, Field

ell.config.verbose = True

 
class Test(BaseModel):
    name: str
    age: int
    height_precise: float
    is_cool: bool

@ell.multimodal(model='gpt-4o-2024-08-06', response_format=Test)
def create_test(text: str):
    """You are a test model. You are given a text and you need to return a pydantic object."""
    return "do it!" 


import json
if __name__ == "__main__":
    result = create_test("ads")
    parsed_result = Test.model_validate_json(result)
    print(parsed_result.model_dump_json(indent=2))


