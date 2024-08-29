import pytest
import os

@pytest.fixture(autouse=True)
def setup_test_env():
    # Set a fake OpenAI API key for all tests
    os.environ['OPENAI_API_KEY'] = 'sk-fake-api-key-for-testing'
    
    # You can add more environment setup here if needed
    
    yield
    
    # Clean up after tests if necessary