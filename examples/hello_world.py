import ell
import math

ell.config.verbose = True


@ell.lm(model="gpt-4o-mini", temperature=0.1)
def reverse_name(name : str):
    return f"Reverse this string: {name}"


def get_user_prompt(world : str):
    return f"Say hello to {world} + {math.pi} with a haiku."

@ell.lm(model="gpt-4o")
def hello(world : str):
    """You are a helpful assistant that writes in lower case.""" # System Message
    return get_user_prompt(reverse_name(world))

if __name__ == "__main__":
    from ell.serializers.filesystem import FilesystemSerializer
    serializer = FilesystemSerializer('./examples_serialized')
    serializer.install()
    print(hello("sama")) # > "hello amas!"