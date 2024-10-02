import ell


@ell.tool()
def get_user_name():
    return "Isac"


@ell.tool()
def get_ice_cream_flavors():
    return ["Vanilla", "Strawberry", "Coconut"]


@ell.complex(model="gpt-4o", tools=[get_user_name, get_ice_cream_flavors])
def f(message_history: list[ell.Message]) -> list[ell.Message]:
    return [
        ell.system(
            "You are a helpful assistant that greets the user and asks them what ice cream flavor they want. Call both tools immediately and then greet the user"
        )
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

    print(messages)