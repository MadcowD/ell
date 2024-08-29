import pytest
import os
from unittest.mock import patch

@pytest.fixture(autouse=True)
def setup_test_env():
    yield
