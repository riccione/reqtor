import responses

from reqtor import API, api_fixture


@responses.activate
def test_api_get_json():
    responses.add(
        responses.GET,
        "https://api.example.com/users/1",
        json={"name": "John"},
        status=200,
    )
    api = API("https://api.example.com")
    api.get("/users/1").expect(200).expect_json({"name": "John"})


@responses.activate
def test_api_post_json():
    responses.add(
        responses.POST,
        "https://api.example.com/users",
        json={"id": 1, "name": "John"},
        status=201,
    )
    api = API("https://api.example.com")
    api.post("/users", json={"name": "John"}).expect(201).expect_json(
        {"id": 1}
    )


@responses.activate
def test_api_put_json():
    responses.add(
        responses.PUT,
        "https://api.example.com/users/1",
        json={"name": "Updated"},
        status=200,
    )
    api = API("https://api.example.com")
    api.put("/users/1", json={"name": "Updated"}).expect(200)


@responses.activate
def test_api_patch_json():
    responses.add(
        responses.PATCH,
        "https://api.example.com/users/1",
        json={"name": "Patched"},
        status=200,
    )
    api = API("https://api.example.com")
    api.patch("/users/1", json={"name": "Patched"}).expect(200)


@responses.activate
def test_api_delete():
    responses.add(
        responses.DELETE, "https://api.example.com/users/1", status=204
    )
    api = API("https://api.example.com")
    api.delete("/users/1").expect(204)


@responses.activate
def test_api_with_token_auth():
    responses.add(
        responses.GET,
        "https://api.example.com/me",
        json={"user": "admin"},
        status=200,
    )
    api = API("https://api.example.com", token="secret-token")
    api.get("/me").expect(200).expect_json({"user": "admin"})

    assert "Authorization" in responses.calls[0].request.headers
    assert (
        responses.calls[0].request.headers["Authorization"]
        == "Bearer secret-token"
    )


@responses.activate
def test_api_with_basic_auth():
    responses.add(
        responses.GET,
        "https://api.example.com/secure",
        json={"ok": True},
        status=200,
    )
    api = API("https://api.example.com", auth=("user", "pass"))
    api.get("/secure").expect(200)


@responses.activate
def test_api_with_custom_headers():
    responses.add(
        responses.GET, "https://api.example.com/data", json={}, status=200
    )
    api = API("https://api.example.com", headers={"X-Custom": "test-value"})
    api.get("/data")

    assert responses.calls[0].request.headers["X-Custom"] == "test-value"


@responses.activate
def test_fluent_chaining_full():
    responses.add(
        responses.GET,
        "https://api.example.com/users/1",
        json={"name": "John", "email": "john@test.com"},
        status=200,
        headers={"X-Request-Id": "abc123"},
    )
    api = API("https://api.example.com")
    (
        api.get("/users/1")
        .expect(200)
        .expect_json({"name": "John"})
        .expect_json_contains("email")
        .expect_header("X-Request-Id", "abc123")
    )


@responses.activate
def test_standard_assertions_style():
    responses.add(
        responses.GET,
        "https://api.example.com/users/1",
        json={"name": "John"},
        status=200,
    )
    api = API("https://api.example.com")
    resp = api.get("/users/1")

    assert resp.status_code == 200
    assert resp.json["name"] == "John"


class TestApiFixture:
    @responses.activate
    def test_api_fixture_returns_client(self):
        responses.add(
            responses.GET,
            "https://api.example.com/health",
            json={"status": "ok"},
            status=200,
        )
        fixture_fn = api_fixture(
            base_url="https://api.example.com", token="test"
        )
        # Call the underlying factory directly via __wrapped__
        api = fixture_fn.__wrapped__()
        api.get("/health").expect(200).expect_json({"status": "ok"})

    def test_api_fixture_requires_base_url(self):
        import pytest

        with pytest.raises(ValueError, match="base_url is required"):
            fixture_fn = api_fixture()
            fixture_fn.__wrapped__()

    def test_api_fixture_env_prefix(self, monkeypatch):
        monkeypatch.setenv("TEST_API_BASE_URL", "https://api.test.com")
        monkeypatch.setenv("TEST_API_TOKEN", "test-token")

        fixture_fn = api_fixture(env_prefix="TEST_API_")
        api = fixture_fn.__wrapped__()

        assert api.base_url == "https://api.test.com"
        assert api.session.headers["Authorization"] == "Bearer test-token"

    def test_api_fixture_env_prefix_missing_url(self, monkeypatch):
        import pytest

        monkeypatch.delenv("MISSING_URL", raising=False)

        fixture_fn = api_fixture(env_prefix="MISSING_")
        with pytest.raises(ValueError, match="MISSING_BASE_URL is not set"):
            fixture_fn.__wrapped__()

    def test_api_fixture_explicit_env_vars(self, monkeypatch):
        monkeypatch.setenv("MY_API_URL", "https://myapi.com")
        monkeypatch.setenv("MY_API_KEY", "my-key")

        fixture_fn = api_fixture(
            base_url_env="MY_API_URL",
            token_env="MY_API_KEY",
        )
        api = fixture_fn.__wrapped__()

        assert api.base_url == "https://myapi.com"
        assert api.session.headers["Authorization"] == "Bearer my-key"

    def test_api_fixture_explicit_env_missing(self, monkeypatch):
        import pytest

        monkeypatch.delenv("NO_SUCH_URL", raising=False)

        fixture_fn = api_fixture(base_url_env="NO_SUCH_URL")
        with pytest.raises(ValueError, match="NO_SUCH_URL is not set"):
            fixture_fn.__wrapped__()

    def test_api_fixture_auth_from_env(self, monkeypatch):
        monkeypatch.setenv("AUTH_USER", "admin")
        monkeypatch.setenv("AUTH_PASS", "secret")

        fixture_fn = api_fixture(
            base_url="https://api.example.com",
            auth_user_env="AUTH_USER",
            auth_pass_env="AUTH_PASS",
        )
        api = fixture_fn.__wrapped__()

        assert api.session.auth == ("admin", "secret")

    def test_api_fixture_auth_from_prefix(self, monkeypatch):
        monkeypatch.setenv("STAGING_BASE_URL", "https://staging.example.com")
        monkeypatch.setenv("STAGING_AUTH_USER", "staging-user")
        monkeypatch.setenv("STAGING_AUTH_PASS", "staging-pass")

        fixture_fn = api_fixture(env_prefix="STAGING_")
        api = fixture_fn.__wrapped__()

        assert api.base_url == "https://staging.example.com"
        assert api.session.auth == ("staging-user", "staging-pass")

    def test_api_fixture_timeout_from_env(self, monkeypatch):
        monkeypatch.setenv("CUSTOM_TIMEOUT", "60")

        fixture_fn = api_fixture(
            base_url="https://api.example.com",
            timeout_env="CUSTOM_TIMEOUT",
        )
        api = fixture_fn.__wrapped__()

        assert api._timeout == 60.0

    def test_api_fixture_headers_from_env(self, monkeypatch):
        import json

        monkeypatch.setenv(
            "CUSTOM_HEADERS", json.dumps({"X-Env-Header": "from-env"})
        )

        fixture_fn = api_fixture(
            base_url="https://api.example.com",
            env_prefix="CUSTOM_",
        )
        api = fixture_fn.__wrapped__()

        assert api.session.headers["X-Env-Header"] == "from-env"

    def test_api_fixture_explicit_overrides_env(self, monkeypatch):
        monkeypatch.setenv("ENV_URL", "https://env.example.com")

        fixture_fn = api_fixture(
            base_url="https://explicit.example.com",
            env_prefix="ENV_",
        )
        api = fixture_fn.__wrapped__()

        assert api.base_url == "https://explicit.example.com"
