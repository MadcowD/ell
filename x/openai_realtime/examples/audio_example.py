import atexit
import asyncio
import base64
import os
from pydub import AudioSegment
import numpy as np
import sounddevice as sd
import threading
import queue
from openai_realtime import RealtimeClient, RealtimeUtils

# Helper function to load and convert audio files


def load_audio_sample(file_path):
    audio = AudioSegment.from_file(file_path)
    samples = np.array(audio.get_array_of_samples())
    return RealtimeUtils.array_buffer_to_base64(samples)

# Function to play audio with buffering


def play_audio(audio_data, sample_rate=24000):
    audio_queue.put(audio_data)


def audio_playback_worker():
    with sd.OutputStream(samplerate=sample_rate, channels=1, dtype='int16') as stream:
        while not stop_event.is_set():
            try:
                data = audio_queue.get(timeout=0.1)
                stream.write(data)
            except queue.Empty:
                continue


# Initialize buffer and threading components
audio_queue = queue.Queue()
stop_event = threading.Event()
sample_rate = 24000  # Ensure this matches your actual sample rate

# Start the background thread for audio playback
playback_thread = threading.Thread(target=audio_playback_worker, daemon=True)
playback_thread.start()

# Ensure to stop the thread gracefully on exit


def cleanup():
    stop_event.set()
    playback_thread.join()


atexit.register(cleanup)


async def main():
    # Initialize the RealtimeClient
    client = RealtimeClient(
        api_key=os.getenv("OPENAI_API_KEY"),
        debug=False
    )

    # Update session with instructions
    client.update_session(
        instructions=(
            ""
        ),
        output_audio_format='pcm16'  # Ensure we get PCM audio output
    )

    # Set up event handler for audio playback
    @client.realtime.on('server.response.audio.delta')
    def handle_audio_delta(event):
        audio_data = np.frombuffer(
            base64.b64decode(event['delta']), dtype=np.int16)
        audio_queue.put(audio_data)

    @client.realtime.on('server.response.text.delta')
    def handle_text_delta(event):
        print(event['delta'], end='', flush=True)

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

    # Wait for and print the assistant's response transcript which happens a bit after the audio is played
    assistant_item = await client.wait_for_next_completed_item()
    print("Assistant's response:", assistant_item)
    client.send_user_message_content(content)
    print("Text sent")
    assistant_item = await client.wait_for_next_completed_item()
    print("Assistant's response:", assistant_item)

    assistant_item = await client.wait_for_next_completed_item()
    print("Assistant's response:", assistant_item)
    # Disconnect from the client
    client.disconnect()
    print("Disconnected from RealtimeClient")

if __name__ == "__main__":
    asyncio.run(main())
