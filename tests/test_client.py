import pytest
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


@responses.activate
class TestAPIRetryOnStatusCodes:
    def test_retry_on_specific_status_codes(self):
        responses.add(
            responses.GET,
            "https://example.com/rate-limited",
            status=429,
        )
        responses.add(
            responses.GET,
            "https://example.com/rate-limited",
            json={"ok": True},
            status=200,
        )
        api = API(
            "https://example.com",
            retries=1,
            backoff_factor=0,
            retry_on={429},
        )
        resp = api.get("/rate-limited")
        assert resp.status_code == 200
        assert len(responses.calls) == 2

    def test_retry_on_multiple_status_codes(self):
        responses.add(
            responses.GET,
            "https://example.com/unavailable",
            status=503,
        )
        responses.add(
            responses.GET,
            "https://example.com/unavailable",
            json={"ok": True},
            status=200,
        )
        api = API(
            "https://example.com",
            retries=1,
            backoff_factor=0,
            retry_on=[429, 503],
        )
        resp = api.get("/unavailable")
        assert resp.status_code == 200
        assert len(responses.calls) == 2

    def test_no_retry_on_unlisted_status_code(self):
        responses.add(
            responses.GET,
            "https://example.com/server-error",
            status=500,
        )
        api = API(
            "https://example.com",
            retries=1,
            backoff_factor=0,
            retry_on={429, 503},
        )
        resp = api.get("/server-error")
        assert resp.status_code == 500
        assert len(responses.calls) == 1

    def test_retry_on_callable(self):
        responses.add(
            responses.GET,
            "https://example.com/transient",
            status=502,
        )
        responses.add(
            responses.GET,
            "https://example.com/transient",
            json={"ok": True},
            status=200,
        )
        api = API(
            "https://example.com",
            retries=1,
            backoff_factor=0,
            retry_on=lambda code: code in (502, 503),
        )
        resp = api.get("/transient")
        assert resp.status_code == 200
        assert len(responses.calls) == 2

    def test_callable_returns_false_no_retry(self):
        responses.add(
            responses.GET,
            "https://example.com/forbidden",
            status=403,
        )
        api = API(
            "https://example.com",
            retries=1,
            backoff_factor=0,
            retry_on=lambda code: code >= 500,
        )
        resp = api.get("/forbidden")
        assert resp.status_code == 403
        assert len(responses.calls) == 1

    def test_default_retry_on_5xx_backward_compat(self):
        responses.add(
            responses.GET,
            "https://example.com/server-error",
            status=500,
        )
        responses.add(
            responses.GET,
            "https://example.com/server-error",
            json={"ok": True},
            status=200,
        )
        api = API("https://example.com", retries=1, backoff_factor=0)
        resp = api.get("/server-error")
        assert resp.status_code == 200
        assert len(responses.calls) == 2


class TestAPIRetryOnException:
    def test_retry_on_exception_callable(self):
        import requests.exceptions

        call_count = 0

        def should_retry(exc):
            nonlocal call_count
            call_count += 1
            return isinstance(exc, requests.exceptions.ConnectionError)

        api = API(
            "https://example.com",
            retries=2,
            backoff_factor=0,
            retry_on_exception=should_retry,
        )
        with pytest.raises(requests.exceptions.ConnectionError):
            with responses.RequestsMock() as rsps:
                rsps.add(
                    responses.GET,
                    "https://example.com/unreachable",
                    body=requests.exceptions.ConnectionError(),
                )
                api.get("/unreachable")
        assert call_count == 2

    def test_exception_not_retryable(self):
        import requests.exceptions

        call_count = 0

        def should_retry(exc):
            nonlocal call_count
            call_count += 1
            return False

        api = API(
            "https://example.com",
            retries=2,
            backoff_factor=0,
            retry_on_exception=should_retry,
        )
        with pytest.raises(requests.exceptions.ConnectionError):
            with responses.RequestsMock() as rsps:
                rsps.add(
                    responses.GET,
                    "https://example.com/unreachable",
                    body=requests.exceptions.ConnectionError(),
                )
                api.get("/unreachable")
        assert call_count == 1

    def test_default_exception_retry_backward_compat(self):
        import requests.exceptions

        api = API(
            "https://example.com",
            retries=1,
            backoff_factor=0,
        )
        with pytest.raises(requests.exceptions.ConnectionError):
            with responses.RequestsMock() as rsps:
                rsps.add(
                    responses.GET,
                    "https://example.com/unreachable",
                    body=requests.exceptions.ConnectionError(),
                )
                api.get("/unreachable")


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


class TestAPIAuth:
    def test_session_has_digest_auth(self):
        from requests.auth import HTTPDigestAuth

        api = API("https://example.com", digest_auth=("user", "pass"))
        assert isinstance(api.session.auth, HTTPDigestAuth)

    def test_session_has_custom_auth_class(self):
        from requests.auth import AuthBase

        class CustomAuth(AuthBase):
            def __call__(self, r):
                r.headers["X-Custom-Auth"] = "token"
                return r

        custom = CustomAuth()
        api = API("https://example.com", auth_class=custom)
        assert api.session.auth is custom

    @responses.activate
    def test_api_key_in_params(self):
        responses.add(
            responses.GET,
            "https://example.com/data",
            json={},
            status=200,
        )
        api = API("https://example.com", api_key="secret123")
        api.get("/data")
        assert "api_key=secret123" in responses.calls[0].request.url

    @responses.activate
    def test_api_key_custom_param_name(self):
        responses.add(
            responses.GET,
            "https://example.com/data",
            json={},
            status=200,
        )
        api = API(
            "https://example.com",
            api_key="key123",
            api_key_param="access_token",
        )
        api.get("/data")
        assert "access_token=key123" in responses.calls[0].request.url

    @responses.activate
    def test_api_key_with_existing_params(self):
        responses.add(
            responses.GET,
            "https://example.com/data",
            json={},
            status=200,
        )
        api = API("https://example.com", api_key="secret123")
        api.get("/data", params={"page": "1"})
        url = responses.calls[0].request.url
        assert "api_key=secret123" in url
        assert "page=1" in url
