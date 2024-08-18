import dataclasses
import ell
from typing import Any, Literal, Type, Union
import pydantic

from ell.stores.sql import SQLiteStore

ell.config.verbose = True


@dataclasses.dataclass
class Add:
    op: Literal["+"]
    a: float
    b: float


@dataclasses.dataclass
class Sub:
    op: Literal["-"]
    a: float
    b: float


@dataclasses.dataclass
class Mul:
    op: Literal["*"]
    a: float
    b: float


@dataclasses.dataclass
class Div:
    op: Literal["/"]
    a: float
    b: float


CalcOp = Union[Add, Sub, Mul, Div]


@ell.lm(model="gpt-4o", temperature=0.1)
def parse_json(task: str, type: Type[Any]):
    return [
        ell.system(
            f"""You are a JSON parser. You respond only in JSON. Do not format using markdown."""
        ),
        ell.user(
            f"""You are given the following task: "{task}"
            Parse the task into the following type:
            {pydantic.TypeAdapter(type).json_schema()}
            """
        )
    ]


def calc_structured(task: str) -> float:
    output = parse_json(task, CalcOp)
    structured = pydantic.TypeAdapter(CalcOp).validate_json(output)
    match structured.op:
        case "+":
            return structured.a + structured.b
        case "-":
            return structured.a - structured.b
        case "*":
            return structured.a * structured.b
        case "/":
            return structured.a / structured.b


if __name__ == "__main__":
    # Local
    ell.init(autocommit=True)

    # API server
    # ell.init(base_url="http://localhost:8080", autocommit=True)

    print(calc_structured("What is two plus two?"))
