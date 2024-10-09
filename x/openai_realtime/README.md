# OpenAI Realtime Python Client (Unofficial)

[![ell2a](https://img.shields.io/badge/ell2a-go)](https://docs.agentbase.space/) [![Discord](https://dcbadge.limes.pink/api/server/vWntgU52Xb?style=flat)](https://discord.gg/vWntgU52Xb) [![X (formerly Twitter) Follow](https://img.shields.io/twitter/follow/wgussml)](https://x.com/wgussml)

This is a Python port of the OpenAI Realtime Client, designed to interact with OpenAI's realtime API for advanced AI interactions.

**Note:** This is a port of OpenAI's realtime client to Python by Xingqiang Chen. For the original version, see [here](https://github.com/openai/openai-realtime-api-beta).

**Note:** This client is designed to be a reference for how ell2a will implement realtime Python bindings. For more information on ell2a, see [ell2a documentation](https://docs.agentbase.space/). Discover the power of ell2a for advanced prompt engineering and seamless integration with OpenAI's realtime API.

## Features

- Realtime communication with OpenAI's API
- Support for text and audio modalities
- Agent integration for extended functionality
- Conversation management and event handling
- Asynchronous operations for improved performance

## Installation

```bash
git clone https://github.com/chenxingqiang/ell2a.git
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

### Adding Custom Agents

```python3
def my_agent_handler(args):
    # Implement your agent logic here
    return {"result": "Agent output"}

client.add_agent(
    {"name": "my_agent", "description": "A custom agent"},
    my_agent_handler
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

For more detailed documentation, please refer to the [API Reference](https://github.com/openai/openai-realtime-api-beta/blob/main/README.md).

## Contributing

Contributions are welcome! This project is a port of the OpenAI Realtime API to Python. Please feel free to submit a Pull Request.

## License and Attribution

This project is licensed under the MIT License, respecting the original license of the OpenAI Realtime API. The original JavaScript implementation can be found at the [OpenAI Realtime API GitHub repository](https://github.com/openai/openai-realtime-api-beta). Special thanks to the OpenAI Realtime API team for their work on the original implementation. For more details, see the LICENSE file.
