import pytest
import asyncio
import os
import base64
from pydub import AudioSegment
import numpy as np

from openai_realtime import RealtimeClient, RealtimeUtils

# Helper function to load and convert audio files


def load_audio_sample(file_path):
    audio = AudioSegment.from_file(file_path)
    samples = np.array(audio.get_array_of_samples())
    return RealtimeUtils.array_buffer_to_base64(samples)


# Sample audio files
samples = {
    'toronto-mp3': './tests/samples/toronto.mp3',
}


@pytest.fixture(scope="module")
def event_loop():
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="module")
async def client():
    client = RealtimeClient(
        api_key=os.getenv("OPENAI_API_KEY"),
        debug=True
    )
    client.update_session(
        instructions=(
            "Please follow the instructions of any query you receive.\n"
            "Be concise in your responses. Speak quickly and answer shortly."
        )
    )
    yield client
    client.disconnect()


async def test_audio_samples(client):
    realtime_events = []
    client.on('realtime.event', lambda event: realtime_events.append(event))

    # Load audio samples
    for key, file_path in samples.items():
        assert os.path.exists(file_path), f"Audio file not found: {file_path}"
        samples[key] = {'filename': file_path,
                       'base64': load_audio_sample(file_path)}

    # Connect to the RealtimeClient
    is_connected = await client.connect()
    assert is_connected == True
    assert client.is_connected() == True

    # Wait for session creation
    await client.wait_for_session_created()

    assert len(realtime_events) == 2
    assert realtime_events[0]['source'] == 'client'
    assert realtime_events[0]['event']['type'] == 'session.update'
    assert realtime_events[1]['source'] == 'server'
    assert realtime_events[1]['event']['type'] == 'session.created'

    print(f"[Session ID] {realtime_events[1]['event']['session']['id']}")

    # Send audio file about Toronto
    sample = samples['toronto-mp3']['base64']
    content = [{'type': 'input_audio', 'audio': sample}]
    client.send_user_message_content(content)

    assert len(realtime_events) == 4
    assert realtime_events[2]['source'] == 'client'
    assert realtime_events[2]['event']['type'] == 'conversation.item.create'
    assert realtime_events[3]['source'] == 'client'
    assert realtime_events[3]['event']['type'] == 'response.create'

    # Wait for user item
    user_item = await client.wait_for_next_item()
    assert user_item['item']['type'] == 'message'
    assert user_item['item']['role'] == 'user'
    assert user_item['item']['status'] == 'completed'
    assert user_item['item']['formatted']['text'] == ''

    # Wait for assistant item
    assistant_item = await client.wait_for_next_item()
    assert assistant_item['item']['type'] == 'message'
    assert assistant_item['item']['role'] == 'assistant'
    assert assistant_item['item']['status'] == 'in_progress'
    assert assistant_item['item']['formatted']['text'] == ''

    # Wait for completed assistant item
    completed_item = await client.wait_for_next_completed_item()
    assert completed_item['item']['type'] == 'message'
    assert completed_item['item']['role'] == 'assistant'
    assert completed_item['item']['status'] == 'completed'
    assert 'toronto' in completed_item['item']['formatted']['transcript'].lower(
    )

if __name__ == "__main__":
    pytest.main([__file__])
