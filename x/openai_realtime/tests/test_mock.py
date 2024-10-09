# x/openai_realtime/tests/test_mock.py
import pytest
from unittest.mock import Mock, patch, AsyncMock
import numpy as np
import json
from openai_realtime.client import RealtimeClient
from openai_realtime.utils import RealtimeUtils


@pytest.fixture
def client():
    client = RealtimeClient()
    client.realtime = Mock()
    client.conversation = Mock()

    # Mock methods within realtime
    client.realtime.connect = AsyncMock(return_value=True)
    client.realtime.send = Mock()
    client.realtime.disconnect = AsyncMock()
    client.realtime.is_connected = Mock(return_value=True)

    # Ensure that send returns a Mock that can have .get called on it
    client.realtime.send.return_value = Mock(get=Mock(return_value=None))

    # Mock methods within conversation
    client.conversation.clear = Mock()

    # Initialize other necessary attributes
    client.input_audio_buffer = np.array([], dtype=np.int16)

    # Ensure session_config is properly initialized
    client._reset_config()

    return client


def test_init(client):
    assert isinstance(client, RealtimeClient)
    assert client.session_created == False
    assert client.agents == {}
    assert client.session_config == client.default_session_config


def test_reset(client):
    client.session_created = True
    client.agents = {'test_agent': {}}
    client.reset()
    assert client.session_created == False
    assert client.agents == {}
    client.realtime.disconnect.assert_called_once()
    client.conversation.clear.assert_called_once()


@pytest.mark.asyncio
async def test_connect(client):
    await client.connect()
    client.realtime.connect.assert_awaited_once()

    expected_session = client.session_config.copy()
    client.realtime.send.assert_called_once_with(
        'session.update', {'session': expected_session})


def test_add_agent(client):
    agent_definition = {'name': 'test_agent', 'description': 'A test agent'}
    agent_handler = Mock()

    client.add_agent(agent_definition, agent_handler)

    assert 'test_agent' in client.agents
    assert client.agents['test_agent']['definition'] == agent_definition
    assert client.agents['test_agent']['handler'] == agent_handler

    expected_session = client.session_config.copy()
    expected_session['agents'] = [{
        'name': 'test_agent',
        'description': 'A test agent',
        'type': 'function'
    }]

    client.realtime.send.assert_called_once_with(
        'session.update', {'session': expected_session})


def test_remove_agent(client):
    # Setup: Add a agent first
    client.agents = {'test_agent': {'definition': {
        'name': 'test_agent', 'description': 'A test agent'}}}

    # Remove the agent
    client.remove_agent('test_agent')

    # Assertions
    assert 'test_agent' not in client.agents

    # Ensure 'session.update' was NOT called automatically
    client.realtime.send.assert_not_called()

    # If session synchronization is needed, it should be done explicitly
    # For example:
    client.update_session()
    expected_session = client.session_config.copy()
    expected_session['agents'] = []

    client.realtime.send.assert_called_once_with(
        'session.update', {'session': expected_session})


def test_delete_item(client):
    client.delete_item('item_id')
    client.realtime.send.assert_called_once_with(
        'conversation.item.delete', {'item_id': 'item_id'})


def test_update_session(client):
    client.update_session(modalities=['text'])
    assert client.session_config['modalities'] == ['text']

    expected_session = client.session_config.copy()

    client.realtime.send.assert_called_once_with(
        'session.update', {'session': expected_session})


def test_send_user_message_content(client):
    content = [{'type': 'text', 'text': 'Hello'}]
    client.send_user_message_content(content)

    expected_calls = [
        ('conversation.item.create', {
            'item': {
                'type': 'message',
                'role': 'user',
                'content': content
            }
        }),
        ('response.create',)
    ]

    assert client.realtime.send.call_count == 2
    client.realtime.send.assert_any_call('conversation.item.create', {
        'item': {
            'type': 'message',
            'role': 'user',
            'content': content
        }
    })
    client.realtime.send.assert_any_call('response.create')


def test_append_input_audio(client):
    audio_data = np.array([1, 2, 3], dtype=np.int16)
    with patch.object(RealtimeUtils, 'array_buffer_to_base64', return_value='base64audio'):
        client.append_input_audio(audio_data)
    client.realtime.send.assert_called_once_with('input_audio_buffer.append', {
        'audio': 'base64audio'
    })
    np.testing.assert_array_equal(client.input_audio_buffer, audio_data)


def test_create_response(client):
    client.create_response()
    client.realtime.send.assert_called_once_with('response.create')


def test_cancel_response(client):
    client.cancel_response()
    client.realtime.send.assert_called_once_with('response.cancel')


@pytest.mark.asyncio
async def test_wait_for_session_created(client):
    client.realtime.is_connected.return_value = True
    client.session_created = False

    # Define a side effect that modifies client.session_created and accepts arguments
    def set_session_created(*args, **kwargs):
        client.session_created = True

    with patch('openai_realtime.client.asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
        mock_sleep.side_effect = set_session_created
        result = await client.wait_for_session_created()

    assert result == True
    mock_sleep.assert_awaited()


@pytest.mark.asyncio
async def test_wait_for_next_item(client):
    client.wait_for_next = AsyncMock(
        return_value={'item': {'id': 'test_item'}})
    result = await client.wait_for_next_item()
    assert result == {'item': {'id': 'test_item'}}
    client.wait_for_next.assert_awaited_once_with('conversation.item.appended')


@pytest.mark.asyncio
async def test_wait_for_next_completed_item(client):
    client.wait_for_next = AsyncMock(
        return_value={'item': {'id': 'test_item', 'status': 'completed'}})
    result = await client.wait_for_next_completed_item()
    assert result == {'item': {'id': 'test_item', 'status': 'completed'}}
    client.wait_for_next.assert_awaited_once_with(
        'conversation.item.completed')


@pytest.mark.asyncio
async def test_call_agent(client):
    agent_name = 'test_agent'
    agent_arguments = '{"arg1": "value1"}'
    agent_result = {'result': 'success'}

    agent_handler_mock = AsyncMock(return_value=agent_result)
    client.agents = {
        agent_name: {
            'handler': agent_handler_mock,
            'definition': {'name': agent_name, 'description': 'A test agent'}
        }
    }

    with patch('json.loads', return_value={'arg1': 'value1'}), \
            patch('json.dumps', return_value=json.dumps(agent_result)):
        await client._call_agent({'name': agent_name, 'arguments': agent_arguments, 'call_id': 'test_call_id'})

    agent_handler_mock.assert_awaited_once_with({'arg1': 'value1'})
    client.realtime.send.assert_any_call('conversation.item.create', {
        'item': {
            'type': 'function_call_output',
            'call_id': 'test_call_id',
            'output': json.dumps(agent_result)
        }
    })
    client.realtime.send.assert_any_call('response.create')


@pytest.mark.asyncio
async def test_call_agent_error(client):
    agent_name = 'test_agent'
    agent_arguments = '{"arg1": "value1"}'
    error_message = "Test error"

    agent_handler_mock = AsyncMock(side_effect=Exception(error_message))
    client.agents = {
        agent_name: {
            'handler': agent_handler_mock,
            'definition': {'name': agent_name, 'description': 'A test agent'}
        }
    }

    with patch('json.loads', return_value={'arg1': 'value1'}), \
            patch('json.dumps', return_value='{"error": "Test error"}'):
        await client._call_agent({'name': agent_name, 'arguments': agent_arguments, 'call_id': 'test_call_id'})

    agent_handler_mock.assert_awaited_once_with({'arg1': 'value1'})
    client.realtime.send.assert_any_call('conversation.item.create', {
        'item': {
            'type': 'function_call_output',
            'call_id': 'test_call_id',
            'output': '{"error": "Test error"}'
        }
    })
    client.realtime.send.assert_any_call('response.create')
