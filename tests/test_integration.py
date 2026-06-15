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
