import ell2a
import random

ell2a.init(store='./logdir', autocommit=True, verbose=True)

def get_random_adjective():
    adjectives = ["enthusiastic", "cheerful", "warm", "friendly", "heartfelt", "sincere"]
    return random.choice(adjectives)

def get_random_punctuation():
    return random.choice(["!", "!!", "!!!"])

@ell2a.simple(model="gpt-4o")
def hello(name: str):
    # """You are a helpful and expressive assistant."""
    adjective = get_random_adjective()
    punctuation = get_random_punctuation()
    return f"Say a {adjective} hello to {name}{punctuation}"

greeting = hello("Sam Altman")
print(greeting)