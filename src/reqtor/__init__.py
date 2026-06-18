"""reqtor - A simple API testing library with dot-notation syntax."""

from reqtor.client import API
from reqtor.fixtures import api_fixture
from reqtor.parametrize import (
    api_endpoints,
    endpoints,
    http_methods,
    statuses,
)
from reqtor.response import Response

__all__ = [
    "API",
    "Response",
    "api_fixture",
    "api_endpoints",
    "endpoints",
    "http_methods",
    "statuses",
]
__version__ = "0.3.0"


def __getattr__(name: str) -> object:
    """Lazy import for async classes (requires httpx)."""
    if name == "AsyncAPI":
        from reqtor.async_client import AsyncAPI

        return AsyncAPI
    if name == "AsyncResponse":
        from reqtor.async_response import AsyncResponse

        return AsyncResponse
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
