import openai
import os

# Define the function to stream the response
def stream_openai_response(prompt):
    try:
        # Make the API call
        response = openai.chat.completions.create(
            model="o1-mini",  # Specify the model
            messages=[{"role": "user", "content": prompt}],
            stream=True  # Enable streaming
        )

        # Stream the response
        for chunk in response:
            if chunk.choices[0].delta.get("content"):
                print(chunk.choices[0].delta.content, end="", flush=True)
        
        print()  # Print a newline at the end

    except Exception as e:
        print(f"An error occurred: {e}")

# Example usage
prompt = "Tell me a short joke."
stream_openai_response(prompt)

# This shows that openai won't fake streaming, it will just fail on the request