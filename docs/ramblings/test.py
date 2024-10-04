''
from typing import Any, Dict, List, TypedDict


class Datapoint(TypedDict, total=False):
    input : Dict[str, Any] | List[Any]


dataset = [
    Datapoint(input=["What is the capital of France?"], ),
]
# XXX: THIS IS SO FUCKING ANNOYING
print(dataset[0]['input'])

# : ( What the fuck,
print(Datapoint(lol="hi"))