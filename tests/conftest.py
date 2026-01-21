import warnings

# Suppress the 32-bit cryptography warning on Windows
warnings.filterwarnings("ignore", category=UserWarning, module="OpenSSL")

import os  # noqa: E402
import sys  # noqa: E402

# Make sure we can import the project modules
# Make sure we can import the project modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import asyncio  # noqa: E402

import pytest  # noqa: E402


@pytest.fixture(scope="function")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()
