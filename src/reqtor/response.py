from __future__ import annotations

import re
from datetime import timedelta
from typing import Any

import requests


def _resolve_path(data: Any, path: str) -> Any:
    """Resolve a dot-notation path against nested data.

    Example: _resolve_path({"user": {"name": "John"}}, "user.name") -> "John"
    """
    keys = path.split(".")
    current = data
    for key in keys:
        assert isinstance(current, dict), (
            f"Cannot traverse into {type(current).__name__} "
            f"at key '{key}' in path '{path}'"
        )
        assert key in current, f"Missing key '{key}' in path '{path}'"
        current = current[key]
    return current


class Response:
    """Wraps requests.Response with fluent assertion methods."""

    def __init__(self, raw: requests.Response) -> None:
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
    def headers(self) -> requests.structures.CaseInsensitiveDict[str]:
        return self._raw.headers

    @property
    def json(self) -> Any:
        return self._raw.json()

    @property
    def elapsed(self) -> timedelta:
        return self._raw.elapsed

    @property
    def ok(self) -> bool:
        return self._raw.ok

    @property
    def raw(self) -> requests.Response:
        return self._raw

    def expect(self, status_code: int) -> Response:
        """Assert status code matches. Returns self for chaining."""
        assert self.status_code == status_code, (
            f"Expected status {status_code}, got {self.status_code}"
        )
        return self

    def expect_ok(self) -> Response:
        """Assert status code is 2xx. Returns self for chaining."""
        assert self.ok, f"Expected 2xx status, got {self.status_code}"
        return self

    def expect_json(self, expected: dict[str, Any]) -> Response:
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

    def expect_json_contains(self, *keys: str) -> Response:
        """Assert JSON contains all specified keys.

        Supports dot-notation for nested keys.
        Example: expect_json_contains("user.name", "user.id")
        """
        data = self.json
        for key in keys:
            _resolve_path(data, key)
        return self

    def expect_json_length(self, key: str, length: int) -> Response:
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

    def expect_json_type(self, key: str, type_: type) -> Response:
        """Assert JSON value at key is of the given type."""
        data = self.json
        value = _resolve_path(data, key)
        assert isinstance(value, type_), (
            f"Key '{key}': expected {type_.__name__}, "
            f"got {type(value).__name__}"
        )
        return self

    def expect_header(self, name: str, value: str | None = None) -> Response:
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

    def expect_no_header(self, name: str) -> Response:
        """Assert header is absent. Returns self for chaining."""
        assert name.lower() not in {k.lower() for k in self.headers}, (
            f"Unexpected header '{name}'"
        )
        return self

    def expect_body(self, expected: str) -> Response:
        """Assert response text equals expected."""
        assert self.text == expected, (
            f"Expected body {expected!r}, got {self.text!r}"
        )
        return self

    def expect_body_contains(self, text: str) -> Response:
        """Assert response body contains the given text."""
        assert text in self.text, (
            f"Expected body to contain {text!r}, got {self.text!r}"
        )
        return self

    def expect_body_matches(self, pattern: str) -> Response:
        """Assert response body matches the given regex."""
        assert re.search(pattern, self.text), (
            f"Expected body to match {pattern!r}, got {self.text!r}"
        )
        return self

    def expect_latency(self, max_seconds: float) -> Response:
        """Assert response time is under max_seconds."""
        actual = self.elapsed.total_seconds()
        assert actual <= max_seconds, (
            f"Expected latency <= {max_seconds}s, got {actual}s"
        )
        return self

    def __repr__(self) -> str:
        return f"Response(status={self.status_code})"
