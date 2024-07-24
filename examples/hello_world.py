import ell
import math

ell.config.verbose = True

@ell.lm(model="gpt-4o-mini")
def hello(world : str):
    """You are helpful assistant"""
    return f"Say hello to {world}!"

if __name__ == "__main__":
    hello("sama") # > "hello sama!"