"""
Pytest for the LM function (mocks the openai api so we can pretend to generate completions through te typoical approach taken in the decorators (and adapters file.))
"""

import pytest
from unittest.mock import patch, MagicMock
from ell.decorators import DEFAULT_SYSTEM_PROMPT, lm
from ell.types import Message, LMPParams


@lm(model="gpt-4-turbo", provider=None, temperature=0.1, max_tokens=5)
def lmp_with_default_system_prompt(*args, **kwargs):
    return "Test user prompt"


@lm(model="gpt-4-turbo", provider=None, temperature=0.1, max_tokens=5)
def lmp_with_docstring_system_prompt(*args, **kwargs):
    """Test system prompt"""  # I personally prefer this sysntax but it's nto formattable so I'm not sure if it's the best approach. I think we can leave this in as a legacy feature but the default docs should be using the ell.system, ell.user, ...

    return "Test user prompt"


@lm(model="gpt-4-turbo", provider=None, temperature=0.1, max_tokens=5)
def lmp_with_message_fmt(*args, **kwargs):
    """Just a normal doc stirng"""

    return [
        Message(role="system", content="Test system prompt from message fmt"),
        Message(role="user", content="Test user prompt 3"),
    ]


@pytest.fixture
def client_mock():
    with patch("ell.adapter.client.chat.completions.create") as mock:
        yield mock


def test_lm_decorator_with_params(client_mock):
    client_mock.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content="Mocked content"))]
    )
    result = lmp_with_default_system_prompt("input", lm_params=dict(temperature=0.5))
    # It should have been called twice
    print("client_mock was called with:", client_mock.call_args)
    client_mock.assert_called_with(
        model="gpt-4-turbo",
        messages=[
            Message(role="system", content=DEFAULT_SYSTEM_PROMPT),
            Message(role="user", content="Test user prompt"),
        ],
        temperature=0.5,
        max_tokens=5,
    )
    assert isinstance(result, str)
    assert result == "Mocked content"


def test_lm_decorator_with_docstring_system_prompt(client_mock):
    client_mock.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content="Mocked content"))]
    )
    result = lmp_with_docstring_system_prompt("input", lm_params=dict(temperature=0.5))
    print("client_mock was called with:", client_mock.call_args)
    client_mock.assert_called_with(
        model="gpt-4-turbo",
        messages=[
            Message(role="system", content="Test system prompt"),
            Message(role="user", content="Test user prompt"),
        ],
        temperature=0.5,
        max_tokens=5,
    )
    assert isinstance(result, str)
    assert result == "Mocked content"

    def test_lm_decorator_with_msg_fmt_system_prompt(client_mock):
        client_mock.return_value = MagicMock(
            choices=[
                MagicMock(message=MagicMock(content="Mocked content from msg fmt"))
            ]
        )
        result = lmp_with_default_system_prompt(
            "input", lm_params=dict(temperature=0.5), message_format="msg fmt"
        )
        print("client_mock was called with:", client_mock.call_args)
        client_mock.assert_called_with(
            model="gpt-4-turbo",
            messages=[
                Message(role="system", content="Test system prompt from message fmt"),
                Message(role="user", content="Test user prompt 3"),  # come on cursor.
            ],
            temperature=0.5,
            max_tokens=5,
        )
        assert isinstance(result, str)
        assert result == "Mocked content from msg fmt"
