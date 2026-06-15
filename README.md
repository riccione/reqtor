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

### `API(base_url, *, headers=None, token=None, auth=None, timeout=30.0)`

HTTP client wrapper. Supports `get`, `post`, `put`, `patch`, `delete`, `head`, `options`.

### `Response` assertions

- `.expect(status_code)` — assert status code
- `.expect_json(dict)` — subset match on JSON body
- `.expect_json_contains(*keys)` — assert keys exist in JSON
- `.expect_header(name, value=None)` — assert header exists/matches
- `.expect_body(text)` — assert exact body match

All assertions return `self` for chaining.

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
