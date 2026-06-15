from __future__ import annotations

from typing import Any

import requests

from reqtor.response import Response


class API:
    """Simple API client with dot-notation syntax for testing."""

    def __init__(
        self,
        base_url: str,
        *,
        headers: dict[str, str] | None = None,
        token: str | None = None,
        auth: tuple[str, str] | None = None,
        timeout: float = 30.0,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._session = requests.Session()
        self._timeout = timeout

        if headers:
            self._session.headers.update(headers)

        if token:
            self._session.headers["Authorization"] = f"Bearer {token}"

        if auth:
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
        resp = self._session.request(
            method,
            self._url(path),
            json=json,
            data=data,
            headers=headers,
            params=params,
            timeout=self._timeout,
            **kwargs,
        )
        return Response(resp)

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
