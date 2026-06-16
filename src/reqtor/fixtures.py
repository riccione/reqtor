from __future__ import annotations

from collections.abc import Callable

from reqtor.client import API


def api_fixture(
    base_url: str,
    *,
    headers: dict[str, str] | None = None,
    token: str | None = None,
    auth: tuple[str, str] | None = None,
    timeout: float = 30.0,
    scope: str = "function",
) -> Callable[..., API]:
    """Create a pytest fixture that provides an API client instance.

    Usage in conftest.py:
        from reqtor import api_fixture
        api = api_fixture(base_url="https://api.example.com", token="xxx")

    Then in tests:
        def test_get_users(api):
            api.get("/users").expect(200)
    """
    import pytest

    @pytest.fixture(scope=scope)
    def fixture(request: pytest.FixtureRequest) -> API:
        return API(
            base_url,
            headers=headers,
            token=token,
            auth=auth,
            timeout=timeout,
        )

    # Store the factory function so tests can call it directly
    def factory() -> API:
        return API(
            base_url,
            headers=headers,
            token=token,
            auth=auth,
            timeout=timeout,
        )

    fixture.__wrapped__ = factory  # type: ignore[attr-defined]
    return fixture
