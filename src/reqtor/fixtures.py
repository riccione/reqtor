from __future__ import annotations

import os
from typing import TYPE_CHECKING

from reqtor.client import API

if TYPE_CHECKING:
    from collections.abc import Callable


def api_fixture(
    base_url: str | None = None,
    *,
    headers: dict[str, str] | None = None,
    token: str | None = None,
    auth: tuple[str, str] | None = None,
    timeout: float = 30.0,
    scope: str = "function",
    env_prefix: str | None = None,
    base_url_env: str | None = None,
    token_env: str | None = None,
    auth_user_env: str | None = None,
    auth_pass_env: str | None = None,
    timeout_env: str | None = None,
) -> Callable[..., API]:
    """Create a pytest fixture that provides an API client instance.

    Supports reading configuration from environment variables for
    multi-environment setups (dev, staging, prod).

    Usage with explicit values (unchanged):
        api = api_fixture(base_url="https://api.example.com", token="xxx")

    Usage with env_prefix (reads from REQTOR_BASE_URL, REQTOR_TOKEN, etc.):
        api = api_fixture(env_prefix="REQTOR_")

    Usage with explicit env var names:
        api = api_fixture(
            base_url_env="MY_API_URL",
            token_env="MY_API_TOKEN",
        )

    Environment variables:
        - {prefix}BASE_URL — API base URL
        - {prefix}TOKEN — Bearer token
        - {prefix}AUTH_USER — Basic auth username
        - {prefix}AUTH_PASS — Basic auth password
        - {prefix}TIMEOUT — Request timeout in seconds
        - {prefix}HEADERS — JSON-encoded headers dict

    Then in tests:
        def test_get_users(api):
            api.get("/users").expect(200)
    """
    import pytest

    def _resolve_config() -> dict:
        """Resolve configuration from explicit values or environment vars."""
        resolved: dict = {}

        # Base URL: explicit > env var > required
        if base_url is not None:
            resolved["base_url"] = base_url
        elif base_url_env:
            val = os.environ.get(base_url_env)
            if val is None:
                raise ValueError(
                    f"Environment variable {base_url_env} is not set"
                )
            resolved["base_url"] = val
        elif env_prefix:
            val = os.environ.get(f"{env_prefix}BASE_URL")
            if val is None:
                raise ValueError(
                    f"Environment variable {env_prefix}BASE_URL is not set"
                )
            resolved["base_url"] = val
        else:
            raise ValueError(
                "base_url is required (pass directly or via env vars)"
            )

        # Token
        resolved_token = token
        if resolved_token is None and token_env:
            resolved_token = os.environ.get(token_env)
        elif resolved_token is None and env_prefix:
            resolved_token = os.environ.get(f"{env_prefix}TOKEN")
        if resolved_token:
            resolved["token"] = resolved_token

        # Auth (user/pass)
        resolved_auth = auth
        if resolved_auth is None and (auth_user_env or auth_pass_env):
            user = os.environ.get(auth_user_env or "", "")
            pw = os.environ.get(auth_pass_env or "", "")
            if user and pw:
                resolved_auth = (user, pw)
        elif resolved_auth is None and env_prefix:
            user = os.environ.get(f"{env_prefix}AUTH_USER")
            pw = os.environ.get(f"{env_prefix}AUTH_PASS")
            if user and pw:
                resolved_auth = (user, pw)
        if resolved_auth:
            resolved["auth"] = resolved_auth

        # Timeout
        resolved_timeout = timeout
        if timeout_env:
            val = os.environ.get(timeout_env)
            if val is not None:
                resolved_timeout = float(val)
        elif env_prefix:
            val = os.environ.get(f"{env_prefix}TIMEOUT")
            if val is not None:
                resolved_timeout = float(val)
        resolved["timeout"] = resolved_timeout

        # Headers
        resolved_headers = dict(headers) if headers else None
        if resolved_headers is None and env_prefix:
            val = os.environ.get(f"{env_prefix}HEADERS")
            if val:
                import json

                resolved_headers = json.loads(val)
        if resolved_headers:
            resolved["headers"] = resolved_headers

        return resolved

    @pytest.fixture(scope=scope)
    def fixture(request: pytest.FixtureRequest) -> API:
        config = _resolve_config()
        return API(
            config["base_url"],
            headers=config.get("headers"),
            token=config.get("token"),
            auth=config.get("auth"),
            timeout=config.get("timeout", timeout),
        )

    # Store the factory function so tests can call it directly
    def factory() -> API:
        config = _resolve_config()
        return API(
            config["base_url"],
            headers=config.get("headers"),
            token=config.get("token"),
            auth=config.get("auth"),
            timeout=config.get("timeout", timeout),
        )

    fixture.__wrapped__ = factory  # type: ignore[attr-defined]
    return fixture
