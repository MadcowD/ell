from pydantic import Field
import ell

ell.init()

@ell.tool()
def get_weather(location: str = Field(description="The full name of a city and country, e.g. San Francisco, CA, USA")):
    """Get the current weather for a given location."""
    # Simulated weather API call
    return f"The weather in {location} is sunny."

@ell.complex(model="gpt-4-turbo", tools=[get_weather])
def travel_planner(destination: str):
    """Plan a trip based on the destination and current weather."""
    return [
        ell.system("You are a travel planner. Use the weather tool to provide relevant advice."),
        ell.user(f"Plan a trip to {destination}")
    ]

result = travel_planner("Paris")
print(result.text)  # Prints travel advice
if result.tool_calls:
    # This is done so that we can pass the tool calls to the language model
    tool_results = result.call_tools_and_collect_as_message()
    print("Weather info:", (tool_results.text))