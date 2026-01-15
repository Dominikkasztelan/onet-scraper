
import warnings
# Suppress the 32-bit cryptography warning on Windows
warnings.filterwarnings("ignore", category=UserWarning, module='OpenSSL')

import pytest
import os
import sys

# Make sure we can import the project modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
