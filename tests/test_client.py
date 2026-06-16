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


@responses.activate
class TestAPIRetries:
    def test_retries_on_500(self):
        responses.add(
            responses.GET,
            "https://example.com/flaky",
            status=500,
        )
        responses.add(
            responses.GET,
            "https://example.com/flaky",
            json={"ok": True},
            status=200,
        )
        api = API("https://example.com", retries=1, backoff_factor=0)
        resp = api.get("/flaky")
        assert resp.status_code == 200
        assert len(responses.calls) == 2

    def test_no_retry_on_400(self):
        responses.add(responses.GET, "https://example.com/bad", status=400)
        api = API("https://example.com", retries=3, backoff_factor=0)
        resp = api.get("/bad")
        assert resp.status_code == 400
        assert len(responses.calls) == 1

    def test_retries_exhausted(self):
        for _ in range(4):
            responses.add(
                responses.GET,
                "https://example.com/fail",
                status=500,
            )
        api = API("https://example.com", retries=2, backoff_factor=0)
        resp = api.get("/fail")
        assert resp.status_code == 500
        assert len(responses.calls) == 3


class TestAPIHooks:
    @responses.activate
    def test_before_hook(self):
        captured = {}

        def before(kwargs):
            captured.update(kwargs)

        responses.add(
            responses.GET,
            "https://example.com/data",
            json={},
            status=200,
        )
        api = API(
            "https://example.com",
            hooks={"before": before},
        )
        api.get("/data")
        assert captured["method"] == "GET"
        assert "/data" in captured["url"]

    @responses.activate
    def test_after_hook(self):
        captured = {}

        def after(resp):
            captured["status"] = resp.status_code

        responses.add(
            responses.GET,
            "https://example.com/data",
            json={},
            status=201,
        )
        api = API(
            "https://example.com",
            hooks={"after": after},
        )
        api.get("/data")
        assert captured["status"] == 201


class TestAPIDebug:
    @responses.activate
    def test_debug_prints_to_stderr(self, capsys):
        responses.add(
            responses.GET,
            "https://example.com/data",
            json={},
            status=200,
        )
        api = API("https://example.com", debug=True)
        api.get("/data")
        captured = capsys.readouterr()
        assert "[reqtor]" in captured.err
        assert "200" in captured.err
