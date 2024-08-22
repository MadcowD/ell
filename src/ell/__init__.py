from ell.lmp.text import text
from ell.lmp.tool import tool
from ell.lmp.multimodal import multimodal
from ell.types import Message, MessageContentBlock
from ell.__version__ import __version__

# registers all of the mdoels.
import ell.models
from ell.configurator import *


def system(content: str) -> Message:
    """
    Create a system message with the given content.

    Args:
    content (str): The content of the system message.

    Returns:
    Message: A Message object with role set to 'system' and the provided content.
    """
    return Message(role="system", content=[MessageContentBlock(text=content)])


def user(content: str) -> Message:
    """
    Create a user message with the given content.

    Args:
    content (str): The content of the user message.

    Returns:
    Message: A Message object with role set to 'user' and the provided content.
    """
    return Message(role="user", content=[MessageContentBlock(text=content)])


def assistant(content: str) -> Message:
    """
    Create an assistant message with the given content.

    Args:
    content (str): The content of the assistant message.

    Returns:
    Message: A Message object with role set to 'assistant' and the provided content.
    """
    return Message(role="assistant", content=[MessageContentBlock(text=content)])


def message(role: str, content: str) -> Message:
    return Message(role=role, content=[MessageContentBlock(text=content)])

__all__ = ["text", "system", "user", "assistant", "config", "__version__"]
