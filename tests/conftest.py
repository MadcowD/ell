import pytest
import os
from unittest.mock import patch

@pytest.fixture(autouse=True)
def setup_test_env():
    # Set a fake OpenAI API key for all tests
    
    # Patch the OpenAI client
    with patch('openai.OpenAI') as mock_openai:
        # Configure the mock client to do nothing
        mock_client = mock_openai.return_value
        mock_client.chat.completions.create.return_value = None
        # exit()
        yield mock_client
    
    # Clean up after tests if necessary