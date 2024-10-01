# OpenAI Realtime Python Client

This is a Python port of the OpenAI Realtime Client, designed to interact with OpenAI's realtime API for advanced AI interactions.

**Note:** This is a port of OpenAI's realtime client to Python by William Guss.

## Features

- Realtime communication with OpenAI's API
- Support for text and audio modalities
- Tool integration for extended functionality
- Conversation management and event handling
- Asynchronous operations for improved performance

## Installation
```bash
git clone https://github.com/MadcowD/ell.git
cd x/openai_realtime
pip install -e .
```
## Quick Start
```python
from openai_realtime import RealtimeClient

async def main():
    client = RealtimeClient(api_key="your-api-key")
    await client.connect()
    
    # Send a text message
    client.send_user_message_content([{"type": "text", "text": "Hello, AI!"}])
    
    # Wait for the AI's response
    response = await client.wait_for_next_completed_item()
    print(response['item']['formatted']['text'])

    client.disconnect()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

## Key Components
- **RealtimeClient**: The main client for interacting with the OpenAI Realtime API.
- **RealtimeAPI**: Handles the WebSocket connection and low-level communication.
- **RealtimeConversation**: Manages the conversation state and message processing.
- **RealtimeEventHandler**: Provides event handling capabilities for the client.
- **RealtimeUtils**: Utility functions for data conversion and manipulation.

## Advanced Usage
### Adding Custom Tools
```python3
def my_tool_handler(args):
    # Implement your tool logic here
    return {"result": "Tool output"}

client.add_tool(
    {"name": "my_tool", "description": "A custom tool"},
    my_tool_handler
)
```

### Handling Audio
```
import numpy as np

# Append audio data
audio_data = np.array([...], dtype=np.int16)
client.append_input_audio(audio_data)

# Create a response (including audio if available)
client.create_response()
```
## Documentation
For more detailed documentation, please refer to the [API Reference](#).

## Contributing
Contributions are welcome! Please feel free to submit a Pull Request.

## License
This project is licensed under the MIT License - see the LICENSE file for details.
