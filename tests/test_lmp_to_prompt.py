# """
# Pytest for the LM function (mocks the openai api so we can pretend to generate completions through the typical approach taken in the decorators (and adapters file.))
# """

# import ell
# from ell.decorators.lm import lm
# import pytest
# from unittest.mock import patch
# from ell.types import Message, LMPParams




# @lm(model="gpt-4-turbo", temperature=0.1, max_tokens=5)
# def lmp_with_docstring_system_prompt(*args, **kwargs):
#     """Test system prompt"""  # I personally prefer this sysntax but it's nto formattable so I'm not sure if it's the best approach. I think we can leave this in as a legacy feature but the default docs should be using the ell.system, ell.user, ...

#     return "Test user prompt"


# @lm(model="gpt-4-turbo", temperature=0.1, max_tokens=5)
# def lmp_with_message_fmt(*args, **kwargs):
#     """Just a normal doc stirng"""

#     return [
#         Message(role="system", content="Test system prompt from message fmt"),
#         Message(role="user", content="Test user prompt 3"),
#     ]


# @pytest.fixture
# def mock_run_lm():
#     with patch("ell.util.lm._run_lm") as mock:
#         mock.return_value = ("Mocked content", None)
#         yield mock


# def test_lm_decorator_with_params(mock_run_lm):
#     result = lmp_with_default_system_prompt("input", api_params=dict(temperature=0.5))
    
#     mock_run_lm.assert_called_once_with(
#         model="gpt-4-turbo",
#         messages=[
#             Message(role="system", content=ell.config.default_system_prompt),
#             Message(role="user", content="Test user prompt"),
#         ],
#         api_params=dict(temperature=0.5, max_tokens=5),
#         _invocation_origin=None,
#         exempt_from_tracking=False,
#         client=None,
#         _logging_color=None,
#     )
#     assert result == "Mocked content"

# @patch("ell.util.lm._run_lm")
# def test_lm_decorator_with_docstring_system_prompt(mock_run_lm):
#     mock_run_lm.return_value = ("Mocked content", None)
#     result = lmp_with_docstring_system_prompt("input", api_params=dict(temperature=0.5))
    
#     mock_run_lm.assert_called_once_with(
#         model="gpt-4-turbo",
#         messages=[
#             Message(role="system", content="Test system prompt"),
#             Message(role="user", content="Test user prompt"),
#         ],
#         api_params=dict(temperature=0.5, max_tokens=5),
#         _invocation_origin=None,
#         exempt_from_tracking=False,
#         client=None,
#         _logging_color=None,
#     )
#     assert result == "Mocked content"

# @patch("ell.util.lm._run_lm")
# def test_lm_decorator_with_msg_fmt_system_prompt(mock_run_lm):
#     mock_run_lm.return_value = ("Mocked content from msg fmt", None)
#     result = lmp_with_message_fmt("input", api_params=dict(temperature=0.5))
    
#     mock_run_lm.assert_called_once_with(
#         model="gpt-4-turbo",
#         messages=[
#             Message(role="system", content="Test system prompt from message fmt"),
#             Message(role="user", content="Test user prompt 3"),
#         ],
#         api_params=dict(temperature=0.5, max_tokens=5),
#         _invocation_origin=None,
#         exempt_from_tracking=False,
#         client=None,
#         _logging_color=None,
#     )
#     assert result == "Mocked content from msg fmt"

# Todo: Figure out mocking.