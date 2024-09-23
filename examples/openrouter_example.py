import logging

import ell
from ell.providers.openrouter import get_client, ProviderPreferences

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Get the OpenRouter client
openrouter_client = get_client()

# Provider Name Alias
ProviderName = ProviderPreferences.ProviderName

@ell.simple(model="meta-llama/llama-3.1-8b-instruct")
def generate_greeting(name: str) -> str:
    """You are a friendly AI assistant."""
    return f"Generate a warm greeting for {name}"


# Example 1: Basic usage without custom preferences
def basic_example():
    greeting = generate_greeting("Sam Altman")
    print(f"Basic Example Greeting: {greeting}")


# Example 2: Using multiple custom preferences
def multiple_preferences_example():
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
    return f"Generate a warm greeting for {name}"


def openai_example():
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
    greeting = generate_greeting_gemini("Sundar Pichai")
    print(f"Gemini Flash Example Greeting: {greeting}")
# -----------------------------------------

# Example 7: Retrieving model parameters
def get_parameters_example():
    model_id = "meta-llama/llama-3.1-8b-instruct"
    parameters = openrouter_client.get_parameters(model_id)
    print(f"Parameters for {model_id}:")
    print(parameters)


# Example 8: Accessing used models
def get_used_models_example():
    # Generate greetings to populate used_models
    if not openrouter_client.used_models:
        generate_greeting("Bill Gates")

    print("Used Models:")
    for model_id, model_info in openrouter_client.used_models.items():
        print(f"Model: {model_id}")
        print(f"  Info: {model_info}")


# Example 9: Getting generation data and comparing provider
def get_generation_data_example():
    # Set provider preferences to use a specific provider with no fallbacks
    desired_provider = ProviderName.HYPERBOLIC
    openrouter_client.set_provider_preferences(ProviderPreferences(
        allow_fallbacks=False,
        order=[desired_provider]
    ))

    # Generate a greeting to get a new generation
    greeting = generate_greeting("Ell")
    print(f"Generation Data Example Greeting: {greeting}")

    # Get the last used model and its generation ID
    last_used_model = next(iter(openrouter_client.used_models.keys()))
    generation_id = openrouter_client.used_models[last_used_model].get('last_message_id')

    if generation_id:
        # Fetch generation data
        generation_data = openrouter_client.get_generation_data(generation_id)

        if 'data' in generation_data:
            provider = generation_data['data'].get('provider_name')
            print(f"Generation Data for model {last_used_model}:")
            print(f"Provider: {provider}")
            print(f"Desired Provider: {desired_provider}")
            print(f"Provider Match: {provider == desired_provider}")
        else:
            print("Generation data not available")
    else:
        print("No generation ID available")


if __name__ == "__main__":
    print("Running examples...")

    basic_example()
    multiple_preferences_example()
    raw_preferences_example()

    # # Uncomment to run OpenAI, Anthropic, and Google examples
    # openai_example()
    # anthropic_example()
    # gemini_example()

    get_generation_data_example()
    get_parameters_example()
    get_used_models_example()

    print("All examples completed.")