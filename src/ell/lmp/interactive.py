from contextlib import contextmanager

from .complex import complex as ell_complex
from ..types import Chat


@contextmanager
def interactive(lmp, messages: List[Message]):
  """Creates an interactive, append-mode session on top of an LMP function."""

  @ell_complex(*args, **kwargs)
  def interactive(messages: Chat) -> Chat:
    return messages

  class _InteractiveSession():
    def __init__(self):
      self._system_prompt = None
      self._messages = messages[:]

    def set_system_prompt(self, prompt):
      self._system_prompt = prompt

    def send(self, message = None):
      if message:
        self._messages.append(message)

      return interactive(
        [self._system_prompt] + self._messages
      )

  sess = _InteractiveSession()

  yield session
