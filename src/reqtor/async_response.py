from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

import httpx

from reqtor.response import _resolve_path

if TYPE_CHECKING:
    from datetime import timedelta


class AsyncResponse:
    """Wraps httpx.Response with fluent assertion methods."""

    def __init__(self, raw: httpx.Response) -> None:
        self._raw = raw

    @property
    def status_code(self) -> int:
        return self._raw.status_code

    @property
    def text(self) -> str:
        return self._raw.text

    @property
    def content(self) -> bytes:
        return self._raw.content

    @property
    def headers(self) -> httpx.Headers:
        return self._raw.headers

    @property
    def json(self) -> Any:
        return self._raw.json()

    @property
    def elapsed(self) -> timedelta:
        return self._raw.elapsed

    @property
    def ok(self) -> bool:
        return 200 <= self.status_code < 300

    @property
    def raw(self) -> httpx.Response:
        return self._raw

    def expect(self, status_code: int) -> AsyncResponse:
        """Assert status code matches. Returns self for chaining."""
        assert self.status_code == status_code, (
            f"Expected status {status_code}, got {self.status_code}"
        )
        return self

    def expect_ok(self) -> AsyncResponse:
        """Assert status code is 2xx. Returns self for chaining."""
        assert self.ok, f"Expected 2xx status, got {self.status_code}"
        return self

    def expect_json(self, expected: dict[str, Any]) -> AsyncResponse:
        """Assert JSON is a superset of expected.

        Supports dot-notation for nested keys.
        Example: expect_json({"user.name": "John"})
        """
        data = self.json
        for key, value in expected.items():
            actual = _resolve_path(data, key)
            assert actual == value, (
                f"Key '{key}': expected {value!r}, got {actual!r}"
            )
        return self

    def expect_json_contains(self, *keys: str) -> AsyncResponse:
        """Assert JSON contains all specified keys.

        Supports dot-notation for nested keys.
        Example: expect_json_contains("user.name", "user.id")
        """
        data = self.json
        for key in keys:
            _resolve_path(data, key)
        return self

    def expect_json_length(self, key: str, length: int) -> AsyncResponse:
        """Assert JSON array at key has the given length."""
        data = self.json
        value = _resolve_path(data, key)
        assert isinstance(value, list), (
            f"Key '{key}': expected list, got {type(value).__name__}"
        )
        assert len(value) == length, (
            f"Key '{key}': expected length {length}, got {len(value)}"
        )
        return self

    def expect_json_type(self, key: str, type_: type) -> AsyncResponse:
        """Assert JSON value at key is of the given type."""
        data = self.json
        value = _resolve_path(data, key)
        assert isinstance(value, type_), (
            f"Key '{key}': expected {type_.__name__}, "
            f"got {type(value).__name__}"
        )
        return self

    def expect_header(
        self, name: str, value: str | None = None
    ) -> AsyncResponse:
        """Assert header exists and optionally matches value."""
        assert name.lower() in {k.lower() for k in self.headers}, (
            f"Missing header '{name}'"
        )
        if value is not None:
            actual = self.headers.get(name)
            assert actual == value, (
                f"Header '{name}': expected {value!r}, got {actual!r}"
            )
        return self

    def expect_no_header(self, name: str) -> AsyncResponse:
        """Assert header is absent. Returns self for chaining."""
        assert name.lower() not in {k.lower() for k in self.headers}, (
            f"Unexpected header '{name}'"
        )
        return self

    def expect_body(self, expected: str) -> AsyncResponse:
        """Assert response text equals expected."""
        assert self.text == expected, (
            f"Expected body {expected!r}, got {self.text!r}"
        )
        return self

    def expect_body_contains(self, text: str) -> AsyncResponse:
        """Assert response body contains the given text."""
        assert text in self.text, (
            f"Expected body to contain {text!r}, got {self.text!r}"
        )
        return self

    def expect_body_matches(self, pattern: str) -> AsyncResponse:
        """Assert response body matches the given regex."""
        assert re.search(pattern, self.text), (
            f"Expected body to match {pattern!r}, got {self.text!r}"
        )
        return self

    def expect_latency(self, max_seconds: float) -> AsyncResponse:
        """Assert response time is under max_seconds."""
        actual = self.elapsed.total_seconds()
        assert actual <= max_seconds, (
            f"Expected latency <= {max_seconds}s, got {actual}s"
        )
        return self

    def __repr__(self) -> str:
        return f"AsyncResponse(status={self.status_code})"
