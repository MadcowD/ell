import ell

from ell import ContentBlock
from PIL import Image
import numpy as np
from ell.types.message import to_content_blocks

@ell.tool()
def get_user_name():
    """
    Return the user's name.
    """
    return "Isac"


def generate_strawberry_image():
    # Create a 200x200 white image
    img = Image.new('RGB', (200, 200), color='white')
    pixels = img.load()

    # Draw a red strawberry shape
    for x in range(200):
        for y in range(200):
            dx = x - 100
            dy = y - 100
            distance = np.sqrt(dx**2 + dy**2)
            if distance < 80:
                # Red color for the body
                pixels[x, y] = (255, 0, 0)
            elif distance < 90 and y < 100:
                # Green color for the leaves
                pixels[x, y] = (0, 128, 0)

    # Add some seeds
    for _ in range(50):
        seed_x = np.random.randint(40, 160)
        seed_y = np.random.randint(40, 160)
        if np.sqrt((seed_x-100)**2 + (seed_y-100)**2) < 80:
            pixels[seed_x, seed_y] = (255, 255, 0)

    return img

@ell.tool()
def get_ice_cream_flavors():
    """
    Return a list of ice cream flavors.
    """
    #XXX: Nice coercion function needed
    return to_content_blocks([("1. Vanilla"), "2.", (generate_strawberry_image()), ("3. Coconut")])


@ell.complex(model="claude-3-5-sonnet-20240620", tools=[get_user_name, get_ice_cream_flavors], max_tokens=1000)
def f(message_history: list[ell.Message]) -> list[ell.Message]:
    return [
        ell.system(
            "You are a helpful assistant that greets the user and asks them what ice cream flavor they want. Call both tools immediately and then greet the user. Some options will be images be sure to interperate them."
        ),
        ell.user("Do it"),
    ] + message_history


if __name__ == "__main__":
    ell.init(verbose=True)
    messages = []
    while True:
        message = f(messages)
        messages.append(message)

        if message.tool_calls:
            tool_call_response = message.call_tools_and_collect_as_message(
                parallel=True, max_workers=2
            )
            messages.append(tool_call_response)
        else:
            break

    # print(messages)