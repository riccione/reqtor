"""Parametrized test helpers for reqtor.

Reduces boilerplate when testing multiple endpoints, status codes,
or HTTP methods.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest

if TYPE_CHECKING:
    from collections.abc import Callable


def endpoints(
    *paths: str,
    method: str = "GET",
    status: int = 200,
    base_url: str = "https://example.com",
    **kwargs: Any,
) -> Callable[..., Any]:
    """Parametrize over multiple endpoints.

    Usage:
        @endpoints("/users", "/posts", "/comments")
        def test_get_endpoints(api, path):
            api.get(path).expect(200)

    With method and status:
        @endpoints("/users", "/posts", method="POST", status=201)
        def test_create_endpoints(api, path):
            api.post(path).expect(201)
    """
    ids = [p.strip("/") for p in paths]
    params = [(p,) for p in paths]
    return pytest.mark.parametrize(
        "path",
        params,
        ids=ids,
    )(lambda func: func)


def statuses(
    *codes: int,
    path: str = "/test",
    method: str = "GET",
    base_url: str = "https://example.com",
) -> Callable[..., Any]:
    """Parametrize over multiple status codes.

    Usage:
        @statuses(200, 201, 204)
        def test_success_statuses(api, status):
            # Mock the endpoint to return this status
            api.get("/test").expect(status)
    """
    params = [(c,) for c in codes]
    return pytest.mark.parametrize(
        "status",
        params,
        ids=[str(c) for c in codes],
    )(lambda func: func)


def http_methods(
    *methods: str,
    path: str = "/test",
    status: int = 200,
) -> Callable[..., Any]:
    """Parametrize over multiple HTTP methods.

    Usage:
        @http_methods("GET", "POST", "PUT", "DELETE")
        def test_http_methods(api, method):
            resp = getattr(api, method.lower())("/test")
            resp.expect(200)
    """
    params = [(m,) for m in methods]
    return pytest.mark.parametrize(
        "method",
        params,
        ids=[m.upper() for m in methods],
    )(lambda func: func)


def api_endpoints(
    *endpoints: tuple[str, int],
    method: str = "GET",
) -> Callable[..., Any]:
    """Parametrize over endpoint-status pairs.

    Usage:
        @api_endpoints(("/users", 200), ("/posts", 200), ("/missing", 404))
        def test_endpoints(api, path, expected_status):
            api.get(path).expect(expected_status)
    """
    params = list(endpoints)
    ids = [f"{path}->{status}" for path, status in endpoints]
    return pytest.mark.parametrize(
        "path,expected_status",
        params,
        ids=ids,
    )(lambda func: func)
