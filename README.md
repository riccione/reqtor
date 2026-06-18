# reqtor

A lightweight Python API testing library with fluent dot-notation assertions.

## Installation

```bash
uv add reqtor

# For async support (httpx-based)
uv add reqtor[async]
```

## Quick Start

```python
from reqtor import API

api = API("https://api.example.com", token="your-token")

# Fluent assertion chaining
api.get("/users/1").expect(200).expect_json({"name": "John"})

# Or use standard assertions
resp = api.post("/users", json={"name": "Jane"})
assert resp.status_code == 201
assert resp.json["name"] == "Jane"
```

## pytest Integration

```python
# conftest.py
from reqtor import api_fixture

api = api_fixture(base_url="https://api.example.com", token="xxx")

# test_api.py
def test_get_users(api):
    api.get("/users").expect(200).expect_json_contains("users")
```

### Multi-environment fixtures

Read configuration from environment variables — no code changes per environment:

```python
# conftest.py
from reqtor import api_fixture

# Reads from REQTOR_BASE_URL, REQTOR_TOKEN, etc.
api = api_fixture(env_prefix="REQTOR_")
```

```bash
# .env.dev
export REQTOR_BASE_URL="https://dev.api.example.com"
export REQTOR_TOKEN="dev-token"

# .env.staging
export REQTOR_BASE_URL="https://staging.api.example.com"
export REQTOR_TOKEN="staging-token"
export REQTOR_AUTH_USER="staging-user"
export REQTOR_AUTH_PASS="staging-pass"
```

Or use explicit env var names:

```python
api = api_fixture(
    base_url_env="MY_API_URL",
    token_env="MY_API_TOKEN",
    auth_user_env="MY_API_USER",
    auth_pass_env="MY_API_PASS",
)
```

Supported environment variables (with `env_prefix="REQTOR_"`):
- `REQTOR_BASE_URL` — API base URL (required)
- `REQTOR_TOKEN` — Bearer token
- `REQTOR_AUTH_USER` / `REQTOR_AUTH_PASS` — Basic auth
- `REQTOR_TIMEOUT` — Request timeout in seconds
- `REQTOR_HEADERS` — JSON-encoded headers dict

## API Reference

### `API(base_url, **kwargs)`

HTTP client wrapper. Supports `get`, `post`, `put`, `patch`, `delete`, `head`, `options`.

**Parameters:**

- `headers` — custom headers dict
- `token` — Bearer token
- `auth` — `(user, pass)` tuple for basic auth
- `digest_auth` — `(user, pass)` tuple for digest auth
- `auth_class` — any `requests.auth.AuthBase` subclass
- `api_key` — API key value to add to query params
- `api_key_param` — query param name for API key (default: `"api_key"`)
- `timeout` — request timeout in seconds (default 30)
- `retries` — number of retries on 5xx/connection errors (default 0)
- `backoff_factor` — exponential backoff multiplier (default 0.5)
- `retry_on` — status codes to retry on: set of ints or callable `(int) -> bool`
- `retry_on_exception` — callable `(Exception) -> bool` to control exception retries
- `hooks` — dict with `"before"` and/or `"after"` callables
- `debug` — print request/response info to stderr

```python
# Bearer token
api = API("https://api.example.com", token="your-token")

# Basic auth
api = API("https://api.example.com", auth=("user", "pass"))

# Digest auth
api = API("https://api.example.com", digest_auth=("user", "pass"))

# API key in query params (?api_key=xxx)
api = API("https://api.example.com", api_key="secret-key")

# Custom param name (?access_token=xxx)
api = API("https://api.example.com", api_key="token", api_key_param="access_token")

# Custom auth class
from requests.auth import HTTPDigestAuth
api = API("https://api.example.com", auth_class=HTTPDigestAuth("u", "p"))

# Full example with retries and hooks
api = API(
    "https://api.example.com",
    token="xxx",
    retries=3,
    backoff_factor=0.5,
    hooks={
        "before": lambda kwargs: print(f"Sending {kwargs['method']}"),
        "after": lambda resp: print(f"Got {resp.status_code}"),
    },
    debug=True,
)

# Retry on specific status codes (e.g., rate limiting)
api = API(
    "https://api.example.com",
    retries=3,
    backoff_factor=0.5,
    retry_on={429, 503},
)

# Retry with custom logic (e.g., retry on any 5xx or 408 Timeout)
api = API(
    "https://api.example.com",
    retries=3,
    retry_on=lambda code: code >= 500 or code == 408,
)

# Custom exception retry logic
api = API(
    "https://api.example.com",
    retries=3,
    retry_on_exception=lambda exc: "timeout" in str(exc).lower(),
)
```

### `Response` assertions

All assertions return `self` for chaining.

**Status:**

- `.expect(status_code)` — assert exact status code
- `.expect_ok()` — assert 2xx status

**JSON (supports dot-notation for nested keys):**

- `.expect_json(dict)` — subset match on JSON body
- `.expect_json_contains(*keys)` — assert keys exist in JSON
- `.expect_json_length(key, n)` — assert array length
- `.expect_json_type(key, type)` — assert value type (`str`, `int`, `list`, etc.)

**Headers:**

- `.expect_header(name, value=None)` — assert header exists/matches
- `.expect_no_header(name)` — assert header is absent

**Body:**

- `.expect_body(text)` — assert exact body match
- `.expect_body_contains(text)` — substring match
- `.expect_body_matches(regex)` — regex match

**Other:**

- `.expect_latency(max_seconds)` — assert response time

```python
from reqtor import API

api = API("https://api.example.com")

# Nested JSON assertions with dot-notation
api.get("/users/1").expect(200).expect_json({
    "user.name": "John",
    "user.address.city": "NYC",
})

# Chaining multiple assertions
(
    api.get("/items")
    .expect_ok()
    .expect_json_contains("data", "total")
    .expect_json_length("data", 10)
    .expect_header("content-type", "application/json")
    .expect_latency(2.0)
)
```

## Request History

Every request made through `API` or `AsyncAPI` is recorded in the `history` property:

```python
api = API("https://api.example.com", retries=2)
api.get("/users")
api.post("/users", json={"name": "Jane"})
api.get("/users/1")

# Inspect all recorded responses
for resp in api.history:
    print(f"{resp.status_code} - {resp.elapsed.total_seconds():.3f}s")

# Check the last request
api.history[-1].expect(200)

# Count failed requests
failed = [r for r in api.history if not r.ok]
```

`history` returns a copy — clearing it won't affect the internal log.

## Parametrized Test Helpers

Reduce boilerplate when testing multiple endpoints, status codes, or HTTP methods:

```python
from reqtor import API, endpoints, statuses, http_methods, api_endpoints

# Test multiple endpoints
@endpoints("/users", "/posts", "/comments")
def test_get_endpoints(api, path):
    api.get(path).expect(200)

# Test multiple status codes
@statuses(200, 201, 204)
def test_success_statuses(api, status):
    api.get("/test").expect(status)

# Test multiple HTTP methods
@http_methods("GET", "POST", "PUT", "DELETE")
def test_http_methods(api, method):
    resp = getattr(api, method.lower())("/test")
    resp.expect(200)

# Test endpoint-status pairs
@api_endpoints(("/users", 200), ("/posts", 200), ("/missing", 404))
def test_endpoints(api, path, expected_status):
    api.get(path).expect(expected_status)
```

## Testing

```bash
# Run mocked tests (default)
pytest

# Run live API tests (hits real external APIs)
pytest -m live

# Run all tests
pytest -m ""
```

Live tests are marked with `@pytest.mark.live` and disabled by default
to avoid unnecessary network calls during development.

## Async Client

For async frameworks (FastAPI, aiohttp), use `AsyncAPI`:

```python
import asyncio
from reqtor import AsyncAPI

async def main():
    async with AsyncAPI("https://api.example.com", token="xxx") as api:
        # Same fluent assertions as sync client
        resp = await api.get("/users/1")
        resp.expect(200).expect_json({"name": "John"})

        # POST with JSON body
        resp = await api.post("/users", json={"name": "Jane"})
        resp.expect(201)

asyncio.run(main())
```

### pytest with async client

```python
import pytest
from reqtor import AsyncAPI

@pytest.mark.asyncio
async def test_get_users():
    async with AsyncAPI("https://api.example.com") as api:
        await api.get("/users").expect(200).expect_json_contains("users")
```

## License

Apache 2.0
