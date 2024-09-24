from dotenv import load_dotenv
load_dotenv()  # Optionally, specify `.env` filepath containing `OPENROUTER_API_KEY`

import os
import ell
from pprint import pprint

# The default openrouter client can be used, with the environment variable `OPENROUTER_API_KEY`
from ell.models.openrouter import client as openrouter_client
from ell.providers import openrouter

# Optionally, specify a new client with custom parameters
custom_client = openrouter.get_client(api_key=os.getenv("OPENROUTER_API_KEY"))

# Provider Aliases
ProviderPreferences = openrouter.ProviderPreferences
ProviderName = ProviderPreferences.ProviderName


@ell.simple(model="meta-llama/llama-3.1-8b-instruct")  # <- `client=openrouter_client` optional here (only one provider)
def generate_greeting(name: str) -> str:
    """You are a friendly AI assistant."""
    return f"Generate a warm, concise greeting for {name}"


# Example 1: Basic usage without custom preferences
def basic_example():
    print("\n--- Example 1: Basic Usage ---")
    greeting = generate_greeting("Sam Altman")
    print(f"Basic Example Greeting: {greeting}")


# Example 2: Using multiple custom preferences
def multiple_preferences_example():
    print("\n--- Example 2: Multiple Provider Preferences ---")
    prefs = ProviderPreferences(
        allow_fallbacks=True,
        data_collection=ProviderPreferences.DataCollectionPolicy.DENY,
        order=[ProviderName.HYPERBOLIC],
        ignore=[ProviderName.LEPTON, ProviderName.NOVITA],
        quantizations=[
            ProviderPreferences.QuantizationLevel.BF16,
            ProviderPreferences.QuantizationLevel.FP8
        ]
    )
    openrouter_client.set_provider_preferences(prefs)
    greeting = generate_greeting("Mark Zuckerberg")
    print(f"Multiple Preferences Example Greeting: {greeting}")


# Example 3: Using raw dictionary for provider preferences
def raw_preferences_example():
    print("\n--- Example 3: Raw Provider Preferences ---")
    raw_prefs = {
        "allow_fallbacks": True,
        "data_collection": "deny",
        "order": ["DeepInfra", "OctoAI"],
        "ignore": ["Fireworks"],
        "quantizations": ["bf16", "fp8"]
    }
    openrouter_client.set_provider_preferences(raw_prefs)
    greeting = generate_greeting("Elon Musk")
    print(f"Raw Preferences Example Greeting: {greeting}")


# Any other OpenRouter models and providers
# -----------------------------------------
# Example 4: Using OpenAI 4o-mini
# We can specify client here, when other providers share the same model
@ell.simple(model="openai/gpt-4o-mini", client=openrouter_client)
def generate_greeting_gpt(name: str) -> str:
    """You are a friendly AI assistant."""
    return f"Generate a warm, concise greeting for {name}"


def openai_example():
    print("\n--- Example 4: OpenAI Usage ---")
    openrouter_client.clear_provider_preferences()
    greeting = generate_greeting_gpt("Satya Nadella")
    print(f"OpenAI Example Greeting: {greeting}")


# Example 5: Using Anthropic Claude Haiku
# We can specify client here, when other providers share the same model
@ell.simple(model="anthropic/claude-3-haiku", client=openrouter_client)
def generate_greeting_claude(name: str) -> str:
    """You are a friendly AI assistant."""
    return f"Generate a warm, concise greeting for a provided name in the form of a Haiku for {name}"

def anthropic_example():
    print("\n--- Example 5: Anthropic Usage ---")
    openrouter_client.clear_provider_preferences()
    greeting = generate_greeting_claude("Jensen Huang")
    print(f"Anthropic Example Greeting: {greeting}")

# Example 6: Using Google Gemini Flash and provider preferences
# We can specify client here, when other providers share the same model
@ell.simple(model="google/gemini-flash-1.5-exp", client=openrouter_client,
            provider_preferences={"data_collection": "allow"})  # <- We can also set provider preferences directly
def generate_greeting_gemini(name: str) -> str:
    """You are a friendly AI assistant."""
    return f"Generate a warm, concise greeting for {name}"

def gemini_example():
    print("\n--- Example 6: Google Gemini Usage ---")
    greeting = generate_greeting_gemini("Sundar Pichai")
    print(f"Gemini Flash Example Greeting: {greeting}")
# -----------------------------------------

# Example 7: Retrieving model parameters
def get_parameters_example():
    print("\n--- Example 7: Retrieving Model Parameters ---")
    model_id = "meta-llama/llama-3.1-8b-instruct"
    parameters = openrouter_client.get_model_parameters(model_id)
    print(f"Parameters for {model_id}:")
    pprint(parameters, width=100, sort_dicts=False)
    return parameters


# Example 8: Accessing used models
def get_used_models_example():
    print("\n--- Example 8: Accessing Used Models ---")
    # Generate greetings to populate used_models
    if not openrouter_client.used_models:
        greeting = generate_greeting("Bill Gates")
        print(f"Get Used Models Example Greeting: {greeting}")

    print("Used Models:")
    pprint(openrouter_client.used_models, width=100, sort_dicts=False)
    return openrouter_client.used_models


# Example 9: Getting generation data and comparing provider
def get_generation_data_example():
    print("\n--- Example 9: Getting Generation Data and Comparing Provider ---")
    # Set provider preferences to use a specific provider with no fallbacks
    desired_provider = ProviderName.HYPERBOLIC
    openrouter_client.set_provider_preferences(ProviderPreferences(
        allow_fallbacks=False,
        order=[desired_provider]
    ))

    # Generate a greeting to get a new generation
    openrouter_client.clear_used_models()
    greeting = generate_greeting("Ell")
    print(f"Generation Data Example Greeting: {greeting}")

    # Get the last used model and its generation ID, then make an API call to fetch non-standard generation data
    last_used_model = next(iter(openrouter_client.used_models.keys()), '')
    generation_id = openrouter_client.used_models.get(last_used_model, {}).get('last_message_id')
    if generation_id:
        generation_data = openrouter_client.get_generation_data(generation_id)
        if generation_data:
            provider = generation_data.get('provider_name')
            print(f"\nGeneration Data for model {last_used_model}:")
            print(f"Provider: {provider}")
            print(f"Desired Provider: {desired_provider}")
            print(f"Provider Match: {provider == desired_provider}")
            print("\nDetailed Generation Data:")
            pprint(generation_data, width=100, sort_dicts=False)
        else:
            print("Generation data not available")
    else:
        print("No generation ID available")


# Example 10: Displaying Global Stats
def get_global_stats_example():
    print("\n--- Example 10: Displaying Global Stats ---")
    if not openrouter_client.used_models:
        greeting = generate_greeting("the World")
        print(f"Global Stats Example Greeting: {greeting}")

    print("\nGlobal Statistics:")
    pprint(openrouter_client.global_stats, width=100, sort_dicts=False)

    print("\nLast Used Model Stats:")
    pprint(openrouter_client.used_models, width=100, sort_dicts=False)


if __name__ == "__main__":
    print("Running examples...")

    basic_example()
    multiple_preferences_example()
    raw_preferences_example()

    # Uncomment to run OpenAI, Anthropic, and Google examples
    # openai_example()
    # anthropic_example()
    # gemini_example()

    get_parameters_example()
    get_used_models_example()
    get_generation_data_example()
    get_global_stats_example()

    print("All examples completed.")