import asyncio
import os
from pydub import AudioSegment
import numpy as np
from openai_realtime import RealtimeClient, RealtimeUtils
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Helper function to load and convert audio files
def load_audio_sample(file_path):
    audio = AudioSegment.from_file(file_path)
    samples = np.array(audio.get_array_of_samples())
    return RealtimeUtils.array_buffer_to_base64(samples)

async def main():
    # Initialize the RealtimeClient
    client = RealtimeClient(
        api_key=os.getenv("OPENAI_API_KEY"),
        debug=True
    )

    # Update session with instructions
    client.update_session(
        instructions=(
            "Please describe the content of the audio you receive.\n"
            "Be concise in your responses. Speak quickly and answer shortly."
        )
    )

    # Connect to the RealtimeClient
    await client.connect()
    print("Connected to RealtimeClient")

    # Wait for session creation
    await client.wait_for_session_created()
    print("Session created")

    # Load audio sample
    audio_file_path = './tests/samples/toronto.mp3'
    audio_sample = load_audio_sample(audio_file_path)

    # Send audio content
    content = [{'type': 'input_audio', 'audio': audio_sample}]
    client.send_user_message_content(content)
    print("Audio sent")

    # Wait for and print the assistant's response
    assistant_item = await client.wait_for_next_completed_item()
    print("Assistant's response:")
    print(assistant_item['item']['formatted']['transcript'])

    # Disconnect from the client
    client.disconnect()
    print("Disconnected from RealtimeClient")

if __name__ == "__main__":
    asyncio.run(main())