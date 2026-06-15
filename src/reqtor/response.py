from __future__ import annotations

from typing import Any

import requests


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
    def elapsed(self) -> Any:
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

    def expect_json(self, expected: dict[str, Any]) -> Response:
        """Assert JSON is a superset of expected."""
        data = self.json
        for key, value in expected.items():
            assert key in data, f"Missing key '{key}' in response JSON"
            assert data[key] == value, (
                f"Key '{key}': expected {value!r}, got {data[key]!r}"
            )
        return self

    def expect_json_contains(self, *keys: str) -> Response:
        """Assert JSON contains all specified keys."""
        data = self.json
        for key in keys:
            assert key in data, f"Missing key '{key}' in response JSON"
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

    def expect_body(self, expected: str) -> Response:
        """Assert response text equals expected. Returns self for chaining."""
        assert self.text == expected, (
            f"Expected body {expected!r}, got {self.text!r}"
        )
        return self

    def __repr__(self) -> str:
        return f"Response(status={self.status_code})"
