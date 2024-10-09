from pydantic import Field
import ell2a

ell2a.init()

@ell2a.agent()
def get_weather(location: str = Field(description="The full name of a city and country, e.g. San Francisco, CA, USA")):
    """Get the current weather for a given location."""
    # Simulated weather API call
    return f"The weather in {location} is sunny."

@ell2a.complex(model="gpt-4-turbo", agents=[get_weather])
def travel_planner(destination: str):
    """Plan a trip based on the destination and current weather."""
    return [
        ell2a.system("You are a travel planner. Use the weather agent to provide relevant advice."),
        ell2a.user(f"Plan a trip to {destination}")
    ]

result = travel_planner("Paris")
print(result.text)  # Prints travel advice
if result.agent_calls:
    # This is done so that we can pass the agent calls to the language model
    agent_results = result.call_agents_and_collect_as_message()
    print("Weather info:", (agent_results.text))