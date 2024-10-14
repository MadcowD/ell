
from functools import wraps
from typing import Generator, Any
# Precanned AI responses for demo purposes
ai_responses = [
    "The capital of France is Paris.",
    "Population: 2200000",
]
        

def lmp(func):
    """
    Decorator that simulates multi-step calls to an LLM API.
    Prints each step and collects all yields from a generator.
    Returns the collected values.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        system_prompt = func.__doc__
        print(f"\033[94mSystem: {system_prompt}\033[0m")
        generator = func(*args, **kwargs)
        message_history = []
        step = 1
        
        try:
            user_prompt = next(generator)
            while True:
                print(f"\033[92mUser: {user_prompt}\033[0m")
                message_history.append({"role": "user", "content": user_prompt})

                # Use precanned AI response
                ai_response = ai_responses[step - 1] if step <= len(ai_responses) else f"AI response for step {step}"
                print(f"\033[93mAssistant: {ai_response}\033[0m")
                
                message_history.append({"role": "assistant", "content": ai_response})
                step += 1

                # Send AI response back to the generator
                user_prompt = generator.send(ai_response)
            
        except StopIteration as e:
            return e.value
    return wrapper

@lmp
def multistep_prompt():
    """You are a helpful assistant."""
    assistant_response = yield "What is the capital of France?"
    print("City!", assistant_response)
    assistant_response_2 = yield "What is the population of that city?"

    # This is allowed in a generator
    return int(assistant_response_2.split("Population: ")[-1])

# Execute the multi-step prompt
result = multistep_prompt()
print(f"{result}")


import asyncio
from functools import wraps

async def async_lmp(func):
    """
    Async decorator that simulates multi-step calls to an LLM API.
    Prints each step and collects all yields from an async generator.
    Returns the collected values.
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        system_prompt = func.__doc__
        print(f"\033[94mSystem: {system_prompt}\033[0m")
        generator = func(*args, **kwargs)
        message_history = []
        step = 1
        
        try:
            user_prompt = await anext(generator)
            while True:
                print(f"\033[92mUser: {user_prompt}\033[0m")
                message_history.append({"role": "user", "content": user_prompt})

                # Use precanned AI response
                ai_response = ai_responses[step - 1] if step <= len(ai_responses) else f"AI response for step {step}"
                print(f"\033[93mAssistant: {ai_response}\033[0m")
                
                message_history.append({"role": "assistant", "content": ai_response})
                step += 1

                # Send AI response back to the generator
                user_prompt = await generator.asend(ai_response)
            
        except StopAsyncIteration as e:
            return e.value
    return wrapper

@async_generator
async def async_multistep_prompt():
    """You are a helpful assistant."""
    resp = await yield_("What is the capital of France?")
    resp = await yield_("What is the population of that city?")
    return int(resp.split("Population: ")[-1])

async def main():
    result = await async_multistep_prompt()
    print(f"{result}")

asyncio.run(main())


# so in some sense this is the most natural interface for ell which is just the fucking api iterface with an lmp context for multistep, the yield statment feels just right for multistep though. it's so unclear to me why async generators do not have a return value though.
@ell.lmp(model="gpt-4o", temperature=0.0, api_params={"max_tokens": 1000})
def my_prompt():
    resp = yield ell.user("What is the capital of France?")

@ell.lmp(model="gpt-4o", temperature=0.0, api_params={"max_tokens": 1000})
def my_prompt():
    resp = yield [ell.user("What is the capital of France?")]

@ell.lmp(model="gpt-4o", temperature=0.0, api_params={"max_tokens": 1000})
def my_prompt():
    resp = yield ell.Call(messages=[ell.user("What is the capital of France?")], api_params={"max_tokens": 10})

@ell.lmp(model="gpt-4o", temperature=0.0, api_params={"max_tokens": 1000})
def my_prompt():
    resp = yield [ell.user("What is the capital of France?")], {"max_tokens": 10}


# This is unacceptable.

@ell.lmp(model="gpt-4o", temperature=0.0, api_params={"max_tokens": 1000})
def my_prompt():
    claude_says = yield "What is the capital of France?", {'model': 'claude'}
    gpt_says = yield "What is the capital of France?"

-->

def normal_prompt():
    anthropic_client = anthropic.Anthropic()
    openai_client = openai.OpenAI()

    claude_says = anthropic_client.messages.create(model="claude-3-opus", messages=[{"role": "user", "content": "What is the capital of France?"}])
    gpt_says = openai_client.chat.completions.create(model="gpt-4o", messages=[
        {"role": "user", "content": "What is the capital of France?"},
        { "role": "assistant", "content": claude_says.content},
        {"role": "user", "content": "What is the capital of France?"}
    ])

    return None



