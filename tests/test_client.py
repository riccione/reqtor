import responses

from reqtor import API


class TestAPIInit:
    def test_base_url_strips_trailing_slash(self):
        api = API("https://example.com/")
        assert api.base_url == "https://example.com"

    def test_base_url_no_trailing_slash(self):
        api = API("https://example.com")
        assert api.base_url == "https://example.com"

    def test_repr(self):
        api = API("https://example.com")
        assert repr(api) == "API(base_url='https://example.com')"

    def test_session_has_token_header(self):
        api = API("https://example.com", token="mytoken")
        assert api.session.headers["Authorization"] == "Bearer mytoken"

    def test_session_has_custom_headers(self):
        api = API("https://example.com", headers={"X-Custom": "value"})
        assert api.session.headers["X-Custom"] == "value"

    def test_session_has_auth(self):
        api = API("https://example.com", auth=("user", "pass"))
        assert api.session.auth == ("user", "pass")


class TestAPIUrlBuilding:
    def test_url_with_leading_slash(self):
        api = API("https://example.com")
        assert api._url("/users") == "https://example.com/users"

    def test_url_without_leading_slash(self):
        api = API("https://example.com")
        assert api._url("users") == "https://example.com/users"

    def test_url_with_nested_path(self):
        api = API("https://example.com")
        assert api._url("/api/v1/users") == "https://example.com/api/v1/users"


@responses.activate
class TestAPIMethods:
    def test_request_returns_response(self):
        responses.add(
            responses.GET, "https://example.com/get", json={}, status=200
        )
        api = API("https://example.com")
        resp = api.request("GET", "/get")
        assert resp.status_code == 200

    def test_get(self):
        responses.add(
            responses.GET, "https://example.com/get", json={}, status=200
        )
        api = API("https://example.com")
        resp = api.get("/get")
        assert resp.status_code == 200

    def test_post(self):
        responses.add(
            responses.POST,
            "https://example.com/post",
            json={"json": {"key": "value"}},
            status=200,
        )
        api = API("https://example.com")
        resp = api.post("/post", json={"key": "value"})
        assert resp.status_code == 200
        assert resp.json["json"] == {"key": "value"}

    def test_put(self):
        responses.add(
            responses.PUT, "https://example.com/put", json={}, status=200
        )
        api = API("https://example.com")
        resp = api.put("/put", json={"key": "value"})
        assert resp.status_code == 200

    def test_patch(self):
        responses.add(
            responses.PATCH, "https://example.com/patch", json={}, status=200
        )
        api = API("https://example.com")
        resp = api.patch("/patch", json={"key": "value"})
        assert resp.status_code == 200

    def test_delete(self):
        responses.add(
            responses.DELETE, "https://example.com/delete", status=200
        )
        api = API("https://example.com")
        resp = api.delete("/delete")
        assert resp.status_code == 200

    def test_head(self):
        responses.add(responses.HEAD, "https://example.com/get", status=200)
        api = API("https://example.com")
        resp = api.head("/get")
        assert resp.status_code == 200

    def test_options(self):
        responses.add(responses.OPTIONS, "https://example.com/get", status=200)
        api = API("https://example.com")
        resp = api.options("/get")
        assert resp.status_code == 200
