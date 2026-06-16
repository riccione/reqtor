# reqtor

A lightweight Python API testing library with fluent dot-notation assertions.

## Installation

```bash
uv add reqtor
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

## API Reference

### `API(base_url, **kwargs)`

HTTP client wrapper. Supports `get`, `post`, `put`, `patch`, `delete`, `head`, `options`.

**Parameters:**

- `headers` — custom headers dict
- `token` — Bearer token
- `auth` — `(user, pass)` tuple for basic auth
- `timeout` — request timeout in seconds (default 30)
- `retries` — number of retries on 5xx/connection errors (default 0)
- `backoff_factor` — exponential backoff multiplier (default 0.5)
- `hooks` — dict with `"before"` and/or `"after"` callables
- `debug` — print request/response info to stderr

```python
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

## License

Apache 2.0
