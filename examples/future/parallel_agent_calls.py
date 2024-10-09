import ell2a


@ell2a.agent()
def get_user_name():
    return "Isac"


@ell2a.agent()
def get_ice_cream_flavors():
    return ["Vanilla", "Strawberry", "Coconut"]


@ell2a.complex(model="gpt-4o", agents=[get_user_name, get_ice_cream_flavors])
def f(message_history: list[ell2a.Message]) -> list[ell2a.Message]:
    return [
        ell2a.system(
            "You are a helpful assistant that greets the user and asks them what ice cream flavor they want. Call both agents immediately and then greet the user"
        )
    ] + message_history


if __name__ == "__main__":
    ell2a.init(verbose=True)
    messages = []
    while True:
        message = f(messages)
        messages.append(message)

        if message.agent_calls:
            agent_call_response = message.call_agents_and_collect_as_message(
                parallel=True, max_workers=2
            )
            messages.append(agent_call_response)
        else:
            break

    print(messages)