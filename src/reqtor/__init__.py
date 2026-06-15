"""reqtor - A simple API testing library with dot-notation syntax."""

from reqtor.client import API
from reqtor.fixtures import api_fixture
from reqtor.response import Response

__all__ = ["API", "Response", "api_fixture"]
__version__ = "0.1.0"
