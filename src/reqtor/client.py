from __future__ import annotations

import sys
import time
from collections.abc import Callable
from typing import Any

import requests

from reqtor.response import Response

# Type for retry_on parameter: callable, collection of status codes, or None
RetryOnStatus = (
    Callable[[int], bool] | set[int] | list[int] | tuple[int, ...] | None
)
RetryOnException = Callable[[Exception], bool] | None


def _should_retry_status(
    status_code: int,
    retry_on: RetryOnStatus,
) -> bool:
    """Check if we should retry based on status code."""
    if retry_on is None:
        return status_code >= 500
    if callable(retry_on):
        return retry_on(status_code)
    return status_code in retry_on


def _should_retry_exception(
    exc: Exception,
    retry_on_exc: RetryOnException,
) -> bool:
    """Check if we should retry based on exception type."""
    if retry_on_exc is None:
        return isinstance(exc, requests.exceptions.ConnectionError)
    return retry_on_exc(exc)


class API:
    """Simple API client with dot-notation syntax for testing."""

    def __init__(
        self,
        base_url: str,
        *,
        headers: dict[str, str] | None = None,
        token: str | None = None,
        auth: tuple[str, str] | None = None,
        digest_auth: tuple[str, str] | None = None,
        auth_class: requests.auth.AuthBase | None = None,
        api_key: str | None = None,
        api_key_param: str = "api_key",
        timeout: float = 30.0,
        retries: int = 0,
        backoff_factor: float = 0.5,
        retry_on: RetryOnStatus = None,
        retry_on_exception: RetryOnException = None,
        hooks: dict[str, Callable[..., Any]] | None = None,
        debug: bool = False,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._session = requests.Session()
        self._timeout = timeout
        self._retries = retries
        self._backoff_factor = backoff_factor
        self._retry_on = retry_on
        self._retry_on_exception = retry_on_exception
        self._hooks = hooks or {}
        self._debug = debug
        self._api_key = api_key
        self._api_key_param = api_key_param

        if headers:
            self._session.headers.update(headers)

        if token:
            self._session.headers["Authorization"] = f"Bearer {token}"

        if auth_class:
            self._session.auth = auth_class
        elif digest_auth:
            from requests.auth import HTTPDigestAuth

            self._session.auth = HTTPDigestAuth(*digest_auth)
        elif auth:
            self._session.auth = auth

    @property
    def base_url(self) -> str:
        return self._base_url

    @property
    def session(self) -> requests.Session:
        return self._session

    def _url(self, path: str) -> str:
        return f"{self._base_url}/{path.lstrip('/')}"

    def request(
        self,
        method: str,
        path: str,
        *,
        json: Any = None,
        data: Any = None,
        headers: dict[str, str] | None = None,
        params: dict[str, str] | None = None,
        **kwargs: Any,
    ) -> Response:
        """Send a request and return a wrapped Response."""
        url = self._url(path)
        kwargs.setdefault("timeout", self._timeout)

        if self._api_key:
            if params is None:
                params = {}
            params[self._api_key_param] = self._api_key

        request_kwargs: dict[str, Any] = {
            "method": method,
            "url": url,
            "json": json,
            "data": data,
            "headers": headers,
            "params": params,
            **kwargs,
        }

        if "before" in self._hooks:
            self._hooks["before"](request_kwargs)

        last_exc: Exception | None = None
        for attempt in range(self._retries + 1):
            try:
                start = time.monotonic()
                resp = self._session.request(**request_kwargs)
                elapsed = time.monotonic() - start

                if self._debug:
                    print(
                        f"[reqtor] {method} {url} "
                        f"-> {resp.status_code} "
                        f"({elapsed:.3f}s)",
                        file=sys.stderr,
                    )

                if (
                    self._retries > 0
                    and _should_retry_status(resp.status_code, self._retry_on)
                    and attempt < self._retries
                ):
                    wait = self._backoff_factor * (2**attempt)
                    time.sleep(wait)
                    continue

                wrapped = Response(resp)

                if "after" in self._hooks:
                    self._hooks["after"](wrapped)

                return wrapped

            except requests.exceptions.ConnectionError as exc:
                last_exc = exc
                if attempt < self._retries and _should_retry_exception(
                    exc, self._retry_on_exception
                ):
                    wait = self._backoff_factor * (2**attempt)
                    time.sleep(wait)
                    continue
                raise

        raise last_exc  # type: ignore[misc]

    def get(self, path: str, **kwargs: Any) -> Response:
        return self.request("GET", path, **kwargs)

    def post(self, path: str, **kwargs: Any) -> Response:
        return self.request("POST", path, **kwargs)

    def put(self, path: str, **kwargs: Any) -> Response:
        return self.request("PUT", path, **kwargs)

    def patch(self, path: str, **kwargs: Any) -> Response:
        return self.request("PATCH", path, **kwargs)

    def delete(self, path: str, **kwargs: Any) -> Response:
        return self.request("DELETE", path, **kwargs)

    def head(self, path: str, **kwargs: Any) -> Response:
        return self.request("HEAD", path, **kwargs)

    def options(self, path: str, **kwargs: Any) -> Response:
        return self.request("OPTIONS", path, **kwargs)

    def __repr__(self) -> str:
        return f"API(base_url={self._base_url!r})"
