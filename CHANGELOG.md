# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.0] - 2026-06-18

### Added

- Async client (`AsyncAPI`) using httpx with context manager support
- Async response assertions (`AsyncResponse`) with full fluent API
- Async response `expect_json_contains()`, `expect_json_length()`, `expect_json_type()`
- Async response `expect_header()`, `expect_no_header()`
- Async response `expect_body()`, `expect_body_contains()`, `expect_body_matches()`
- Async response `expect_latency()`
- pytest-asyncio integration with `respx` for async mocking
- Lazy async imports via `__getattr__` in `__init__.py`
- 130 tests passing, 92.45% coverage

## [0.1.0] - 2026-06-17

### Added

- Core `API` class with HTTP verb shortcuts (get, post, put, patch, delete, head, options)
- `Response` wrapper with fluent assertion methods
- Authentication support:
  - Bearer token (`token` parameter)
  - Basic auth (`auth` parameter)
  - Digest auth (`digest_auth` parameter)
  - Custom auth classes (`auth_class` parameter)
  - API key in query params (`api_key` and `api_key_param` parameters)
- JSON assertions with dot-notation for nested keys
- Response assertions:
  - `expect()` — exact status code
  - `expect_ok()` — 2xx status
  - `expect_json()` — JSON subset match
  - `expect_json_contains()` — JSON key presence
  - `expect_json_length()` — array length
  - `expect_json_type()` — value type
  - `expect_header()` — header presence/value
  - `expect_no_header()` — header absence
  - `expect_body()` — exact body match
  - `expect_body_contains()` — substring match
  - `expect_body_matches()` — regex match
  - `expect_latency()` — response time
- Client features:
  - Retry with exponential backoff on 5xx/connection errors
  - Before/after request hooks
  - Debug mode with request/response logging
- pytest integration:
  - `api_fixture()` factory for creating pytest fixtures
  - `@pytest.mark.live` marker for real API tests
- CI/CD pipeline with GitHub Actions (lint + test)
- Test coverage reporting with pytest-cov (92% coverage)
- Live API tests using catfact.ninja

### Changed

- Made pytest an optional dependency (core works without pytest installed)

### Fixed

- Resolved ruff warnings TC003 (type-checking imports) and A004 (shadowed builtin)

## [0.0.1] - 2026-06-16

### Added

- Initial project setup
- Project configuration with hatchling and uv
- Ruff linter/formatter configuration
- Basic README

[Unreleased]: https://github.com/riccione/reqtor/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/riccione/reqtor/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/riccione/reqtor/compare/v0.0.1...v0.1.0
[0.0.1]: https://github.com/riccione/reqtor/releases/tag/v0.0.1
