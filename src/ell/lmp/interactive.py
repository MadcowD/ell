from contextlib import contextmanager

from .complex import complex as ell_complex
from ..types.message import system as ell_system, user as ell_user


@contextmanager
def interactive(*args, **kwargs):
    """A contextmanager that creates an interactive, append-mode session using an inline LMP function."""

    # TODO(kwlzn): Should this be specified/impl'd a different way for better viz/tracking in ell studio?
    @ell_complex(*args, **kwargs)
    def interactive(messages):
        return messages

    class _InteractiveSession():
        def __init__(self):
            self._system_prompt = None
            self._messages = []
            self._last_response = None

        def set_system_prompt(self, prompt):
            self._system_prompt = ell_system(prompt)

        def send(self, message = None):
            if message:
                self._messages.append(ell_user(message))

            # Invoke the LMP function.
            self._last_response = interactive([self._system_prompt] + self._messages)

            # Append the role="assistant" response to the messages.
            self._messages.append(self._last_response)

            # If we have a tool call, invoke it and append the tool call result as a user message.
            if (tool_call_messages := self._last_response.call_tools_and_collect_as_message()):
              self._messages.append(tool_call_messages)
              self.send()

            return self._last_response

    yield _InteractiveSession()
