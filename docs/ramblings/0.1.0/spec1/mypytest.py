from typing import TypedDict


class Test(TypedDict):
    name: str
    age: int


def test(**t: Test):
    print(t)

# no type hinting like ts thats unfortunate.
test( )
