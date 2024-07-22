from ell.util.closure import lexically_closured_source

class Test:
    pass

X = 6


def another_function():
    return X

def test():
    return another_function()


if __name__ == "__main__":
    (src, depencied) , etc = (lexically_closured_source(test))
    print("Source:")
    print(src)
    print("Dependencies:")
    print(depencied)
