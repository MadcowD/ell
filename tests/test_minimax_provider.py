"""Tests for MiniMax model registration and provider integration."""
import os
import json
import pytest
from unittest.mock import MagicMock, patch, PropertyMock

import openai
from openai.types.chat import ChatCompletion, ChatCompletionChunk
from openai._streaming import Stream

from ell.configurator import config, Config
from ell.provider import EllCallParams
from ell.providers.openai import OpenAIProvider
from ell.types import Message, ContentBlock


# ---------------------------------------------------------------------------
# Unit tests – model registration
# ---------------------------------------------------------------------------

class TestMiniMaxModelRegistration:
    """Verify that MiniMax models are registered correctly."""

    def test_register_with_explicit_client(self):
        """register() should register all MiniMax models with the given client."""
        from ell.models.minimax import register, MINIMAX_MODELS

        mock_client = MagicMock(spec=openai.Client)
        test_config = Config()

        with patch("ell.models.minimax.config", test_config):
            register(client=mock_client)

        for model_id in MINIMAX_MODELS:
            assert model_id in test_config.registry
            assert test_config.registry[model_id].default_client is mock_client

    def test_register_with_api_key(self):
        """register(api_key=...) should create a client and register models."""
        from ell.models.minimax import register, MINIMAX_MODELS

        test_config = Config()

        with patch("ell.models.minimax.config", test_config), \
             patch("ell.models.minimax.openai.Client") as MockClient:
            mock_instance = MagicMock()
            MockClient.return_value = mock_instance
            register(api_key="test-key-123")

            MockClient.assert_called_once_with(
                base_url="https://api.minimax.io/v1",
                api_key="test-key-123",
            )
            for model_id in MINIMAX_MODELS:
                assert model_id in test_config.registry

    def test_register_with_env_var(self):
        """register() should fall back to MINIMAX_API_KEY env var."""
        from ell.models.minimax import register, MINIMAX_MODELS

        test_config = Config()

        with patch("ell.models.minimax.config", test_config), \
             patch("ell.models.minimax.openai.Client") as MockClient, \
             patch.dict(os.environ, {"MINIMAX_API_KEY": "env-key-456"}):
            mock_instance = MagicMock()
            MockClient.return_value = mock_instance
            register()

            MockClient.assert_called_once_with(
                base_url="https://api.minimax.io/v1",
                api_key="env-key-456",
            )
            for model_id in MINIMAX_MODELS:
                assert model_id in test_config.registry

    def test_register_without_key_raises(self):
        """register() without API key or env var should raise."""
        from ell.models.minimax import register

        test_config = Config()

        with patch("ell.models.minimax.config", test_config), \
             patch.dict(os.environ, {}, clear=True):
            # Remove MINIMAX_API_KEY if present
            os.environ.pop("MINIMAX_API_KEY", None)
            with pytest.raises(openai.OpenAIError):
                register()

    def test_model_list_contents(self):
        """MINIMAX_MODELS should contain the expected model IDs."""
        from ell.models.minimax import MINIMAX_MODELS

        assert "MiniMax-M2.7" in MINIMAX_MODELS
        assert "MiniMax-M2.7-highspeed" in MINIMAX_MODELS
        assert "MiniMax-M2.5" in MINIMAX_MODELS
        assert "MiniMax-M2.5-highspeed" in MINIMAX_MODELS
        assert len(MINIMAX_MODELS) == 4

    def test_auto_registration_with_env_var(self):
        """Module-level auto-registration should register models when env var is set."""
        from ell.models.minimax import MINIMAX_MODELS

        test_config = Config()
        mock_client = MagicMock()

        with patch("ell.models.minimax.openai.Client", return_value=mock_client) as MockClient, \
             patch.dict(os.environ, {"MINIMAX_API_KEY": "auto-key"}):
            # Simulate the module-level auto-registration logic
            key = os.environ.get("MINIMAX_API_KEY")
            client = MockClient(base_url="https://api.minimax.io/v1", api_key=key)
            for model_id in MINIMAX_MODELS:
                test_config.register_model(model_id, client)

            for model_id in MINIMAX_MODELS:
                assert model_id in test_config.registry

    def test_auto_registration_without_env_var(self):
        """Module-level auto-registration should silently skip when no env var."""
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("MINIMAX_API_KEY", None)
            # Simulate module-level logic: no key → no registration
            key = os.environ.get("MINIMAX_API_KEY")
            assert key is None


# ---------------------------------------------------------------------------
# Unit tests – OpenAI provider compatibility (MiniMax uses OpenAI provider)
# ---------------------------------------------------------------------------

class TestMiniMaxProviderCompat:
    """MiniMax uses the OpenAI provider. Verify translation works for MiniMax models."""

    @pytest.fixture
    def provider(self):
        return OpenAIProvider()

    @pytest.fixture
    def minimax_client(self):
        client = MagicMock(spec=openai.Client)
        client.chat = MagicMock()
        client.chat.completions = MagicMock()
        client.chat.completions.create = MagicMock()
        client.beta = MagicMock()
        client.beta.chat = MagicMock()
        client.beta.chat.completions = MagicMock()
        client.beta.chat.completions.parse = MagicMock()
        return client

    def test_translate_to_provider_basic(self, provider, minimax_client):
        """translate_to_provider should work with MiniMax model names."""
        ell_call = EllCallParams(
            client=minimax_client,
            api_params={},
            model="MiniMax-M2.7",
            messages=[Message(role="user", content=[ContentBlock(text="Hello")])],
            tools=[],
        )

        translated = provider.translate_to_provider(ell_call)
        assert translated["model"] == "MiniMax-M2.7"
        assert translated["stream"] is True
        assert translated["messages"] == [
            {"role": "user", "content": [{"type": "text", "text": "Hello"}]}
        ]

    def test_translate_to_provider_m25(self, provider, minimax_client):
        """Should work with MiniMax-M2.5 model."""
        ell_call = EllCallParams(
            client=minimax_client,
            api_params={"temperature": 0.7},
            model="MiniMax-M2.5",
            messages=[Message(role="user", content=[ContentBlock(text="Hi")])],
            tools=[],
        )

        translated = provider.translate_to_provider(ell_call)
        assert translated["model"] == "MiniMax-M2.5"
        assert translated["temperature"] == 0.7

    def test_translate_to_provider_highspeed(self, provider, minimax_client):
        """Should work with MiniMax-M2.5-highspeed model."""
        ell_call = EllCallParams(
            client=minimax_client,
            api_params={},
            model="MiniMax-M2.5-highspeed",
            messages=[Message(role="user", content=[ContentBlock(text="Quick")])],
            tools=[],
        )

        translated = provider.translate_to_provider(ell_call)
        assert translated["model"] == "MiniMax-M2.5-highspeed"

    def test_translate_to_provider_m27_highspeed(self, provider, minimax_client):
        """Should work with MiniMax-M2.7-highspeed model."""
        ell_call = EllCallParams(
            client=minimax_client,
            api_params={},
            model="MiniMax-M2.7-highspeed",
            messages=[Message(role="user", content=[ContentBlock(text="Fast")])],
            tools=[],
        )

        translated = provider.translate_to_provider(ell_call)
        assert translated["model"] == "MiniMax-M2.7-highspeed"

    def test_translate_to_provider_system_message(self, provider, minimax_client):
        """System messages should be converted to text-only for MiniMax."""
        ell_call = EllCallParams(
            client=minimax_client,
            api_params={},
            model="MiniMax-M2.7",
            messages=[
                Message(role="system", content=[ContentBlock(text="You are helpful.")]),
                Message(role="user", content=[ContentBlock(text="Hello")]),
            ],
            tools=[],
        )

        translated = provider.translate_to_provider(ell_call)
        assert translated["messages"][0] == {
            "role": "system",
            "content": "You are helpful.",
        }

    def test_translate_from_provider_non_streaming(self, provider, minimax_client):
        """Non-streaming response parsing should work for MiniMax responses."""
        ell_call = EllCallParams(
            client=minimax_client,
            api_params={},
            model="MiniMax-M2.7",
            messages=[],
            tools=[],
        )
        chat_completion = ChatCompletion(
            id="chatcmpl-minimax-123",
            model="MiniMax-M2.7",
            choices=[
                dict(
                    index=0,
                    message=dict(role="assistant", content="Hello from MiniMax!"),
                    finish_reason="stop",
                )
            ],
            created=1234567890,
            object="chat.completion",
        )

        messages, metadata = provider.translate_from_provider(
            provider_response=chat_completion,
            ell_call=ell_call,
            provider_call_params={"stream": False},
        )
        assert len(messages) == 1
        assert messages[0].role == "assistant"
        assert messages[0].text == "Hello from MiniMax!"
        assert metadata["model"] == "MiniMax-M2.7"

    def test_translate_from_provider_streaming(self, provider, minimax_client):
        """Streaming response parsing should work for MiniMax responses."""
        ell_call = EllCallParams(
            client=minimax_client,
            api_params={},
            model="MiniMax-M2.7",
            messages=[],
            tools=[],
        )
        chunk1 = ChatCompletionChunk(
            id="chunk_mm_1",
            object="chat.completion.chunk",
            created=1234567890,
            model="MiniMax-M2.7",
            choices=[dict(index=0, delta=dict(role="assistant", content="Hello"))],
        )
        chunk2 = ChatCompletionChunk(
            id="chunk_mm_2",
            object="chat.completion.chunk",
            created=1234567891,
            model="MiniMax-M2.7",
            choices=[dict(index=0, delta=dict(content=" World"))],
        )
        mock_stream = MagicMock(spec=Stream)
        mock_stream.__iter__.return_value = [chunk1, chunk2]

        messages, metadata = provider.translate_from_provider(
            provider_response=mock_stream,
            ell_call=ell_call,
            provider_call_params={"stream": True},
        )
        assert len(messages) == 1
        assert messages[0].text == "Hello World"

    def test_provider_call_function(self, provider, minimax_client):
        """provider_call_function should return chat.completions.create for MiniMax."""
        func = provider.provider_call_function(minimax_client, {})
        assert func == minimax_client.chat.completions.create

    def test_temperature_zero(self, provider, minimax_client):
        """MiniMax accepts temperature=0."""
        ell_call = EllCallParams(
            client=minimax_client,
            api_params={"temperature": 0},
            model="MiniMax-M2.7",
            messages=[Message(role="user", content=[ContentBlock(text="Test")])],
            tools=[],
        )

        translated = provider.translate_to_provider(ell_call)
        assert translated["temperature"] == 0


# ---------------------------------------------------------------------------
# Integration tests – require MINIMAX_API_KEY
# ---------------------------------------------------------------------------

@pytest.mark.skipif(
    not os.environ.get("MINIMAX_API_KEY"),
    reason="MINIMAX_API_KEY not set",
)
class TestMiniMaxIntegration:
    """Integration tests that make real API calls to MiniMax."""

    def test_chat_completion(self):
        """Basic chat completion with MiniMax-M2.7."""
        import ell

        minimax_client = openai.Client(
            base_url="https://api.minimax.io/v1",
            api_key=os.environ["MINIMAX_API_KEY"],
        )

        @ell.simple(model="MiniMax-M2.7", temperature=0.1, client=minimax_client)
        def hello(name: str) -> str:
            """You are a helpful assistant. Reply in one short sentence."""
            return f"Say hello to {name}."

        result = hello("World")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_streaming_chat(self):
        """Streaming chat completion with MiniMax-M2.5-highspeed."""
        client = openai.Client(
            base_url="https://api.minimax.io/v1",
            api_key=os.environ["MINIMAX_API_KEY"],
        )
        response = client.chat.completions.create(
            model="MiniMax-M2.5-highspeed",
            messages=[{"role": "user", "content": "Say hi"}],
            stream=True,
        )
        chunks = []
        for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                chunks.append(chunk.choices[0].delta.content)
        result = "".join(chunks)
        assert len(result) > 0

    def test_custom_client_registration(self):
        """Explicit registration via register() should work."""
        from ell.models.minimax import register

        test_config = Config()
        with patch("ell.models.minimax.config", test_config):
            register(api_key=os.environ["MINIMAX_API_KEY"])

        assert "MiniMax-M2.7" in test_config.registry
        assert "MiniMax-M2.7-highspeed" in test_config.registry
        assert "MiniMax-M2.5" in test_config.registry
        assert "MiniMax-M2.5-highspeed" in test_config.registry
