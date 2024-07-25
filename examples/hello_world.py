import ell
import math

from ell.stores.sql import SQLiteStore

ell.config.verbose = True

@ell.lm(model="gpt-4o-mini")
def hello(world : str):
    """You are helpful assistant"""
    return f"Say hello to  asdasd asd asd  {world[::-1]}!"

if __name__ == "__main__":

    store = SQLiteStore('sqlite_example')
    store.install()
    hello("sama") # > "hello sama!"



