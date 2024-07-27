import pytest
from ell.types import Message


@pytest.fixture
def message():
    return Message(role="user", content="Initial content")


def test_initialization():
    """Test that the dictionary is correctly initialized with dataclass fields."""
    msg = Message(role="admin", content="Hello, world!")
    assert msg["role"] == "admin"
    assert msg["content"] == "Hello, world!"
    assert msg.role == "admin"
    assert msg.content == "Hello, world!"


def test_attribute_modification(message):
    """Test that modifications to attributes update the dictionary."""
    # Modify the attributes
    message.role = "moderator"
    message.content = "Updated content"
    # Check dictionary synchronization
    assert message["role"] == "moderator"
    assert message["content"] == "Updated content"
    assert message.role == "moderator"
    assert message.content == "Updated content"


def test_dictionary_modification(message):
    """Test that direct dictionary modifications do not break attribute access."""
    # Directly modify the dictionary
    message["role"] = "admin"
    message["content"] = "New content"
    # Check if the attributes are not affected (they should not be, as this is one-way sync)
    assert message.role == "user"
    assert message.content == "Initial content"
    assert message["role"] == "admin"
    assert message["content"] == "New content"
