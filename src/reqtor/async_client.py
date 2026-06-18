from __future__ import annotations

import sys
import time
from typing import TYPE_CHECKING, Any

import httpx

from reqtor.async_response import AsyncResponse
from reqtor.client import (
    RetryOnException,
    RetryOnStatus,
    _should_retry_exception,
    _should_retry_status,
)

if TYPE_CHECKING:
    from collections.abc import Callable


class AsyncAPI:
    """Async API client with dot-notation syntax for testing."""

    def __init__(
        self,
        base_url: str,
        *,
        headers: dict[str, str] | None = None,
        token: str | None = None,
        auth: tuple[str, str] | None = None,
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
        self._timeout = timeout
        self._retries = retries
        self._backoff_factor = backoff_factor
        self._retry_on = retry_on
        self._retry_on_exception = retry_on_exception
        self._hooks = hooks or {}
        self._debug = debug
        self._api_key = api_key
        self._api_key_param = api_key_param
        self._history: list[AsyncResponse] = []

        merged_headers = dict(headers) if headers else {}
        if token:
            merged_headers["Authorization"] = f"Bearer {token}"

        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            headers=merged_headers,
            auth=httpx.BasicAuth(*auth) if auth else None,
            timeout=timeout,
        )

    @property
    def base_url(self) -> str:
        return self._base_url

    @property
    def client(self) -> httpx.AsyncClient:
        return self._client

    @property
    def history(self) -> list[AsyncResponse]:
        """Return all responses recorded during this session."""
        return list(self._history)

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        await self._client.aclose()

    async def __aenter__(self) -> AsyncAPI:
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()

    def _url(self, path: str) -> str:
        return f"/{path.lstrip('/')}"

    async def request(
        self,
        method: str,
        path: str,
        *,
        json: Any = None,
        data: Any = None,
        headers: dict[str, str] | None = None,
        params: dict[str, str] | None = None,
        **kwargs: Any,
    ) -> AsyncResponse:
        """Send a request and return a wrapped AsyncResponse."""
        url = self._url(path)

        if self._api_key:
            if params is None:
                params = {}
            params[self._api_key_param] = self._api_key

        request_kwargs: dict[str, Any] = {
            "method": method,
            "url": url,
            "json": json,
            "content": data,
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
                resp = await self._client.request(**request_kwargs)
                elapsed = time.monotonic() - start

                if self._debug:
                    print(
                        f"[reqtor] {method} {self._base_url}{url} "
                        f"-> {resp.status_code} "
                        f"({elapsed:.3f}s)",
                        file=sys.stderr,
                    )

                if (
                    self._retries > 0
                    and _should_retry_status(resp.status_code, self._retry_on)
                    and attempt < self._retries
                ):
                    import asyncio

                    wait = self._backoff_factor * (2**attempt)
                    await asyncio.sleep(wait)
                    continue

                wrapped = AsyncResponse(resp)
                self._history.append(wrapped)

                if "after" in self._hooks:
                    self._hooks["after"](wrapped)

                return wrapped

            except httpx.ConnectError as exc:
                last_exc = exc
                if attempt < self._retries and _should_retry_exception(
                    exc, self._retry_on_exception
                ):
                    import asyncio

                    wait = self._backoff_factor * (2**attempt)
                    await asyncio.sleep(wait)
                    continue
                raise

        raise last_exc  # type: ignore[misc]

    async def get(self, path: str, **kwargs: Any) -> AsyncResponse:
        return await self.request("GET", path, **kwargs)

    async def post(self, path: str, **kwargs: Any) -> AsyncResponse:
        return await self.request("POST", path, **kwargs)

    async def put(self, path: str, **kwargs: Any) -> AsyncResponse:
        return await self.request("PUT", path, **kwargs)

    async def patch(self, path: str, **kwargs: Any) -> AsyncResponse:
        return await self.request("PATCH", path, **kwargs)

    async def delete(self, path: str, **kwargs: Any) -> AsyncResponse:
        return await self.request("DELETE", path, **kwargs)

    async def head(self, path: str, **kwargs: Any) -> AsyncResponse:
        return await self.request("HEAD", path, **kwargs)

    async def options(self, path: str, **kwargs: Any) -> AsyncResponse:
        return await self.request("OPTIONS", path, **kwargs)

    def __repr__(self) -> str:
        return f"AsyncAPI(base_url={self._base_url!r})"
