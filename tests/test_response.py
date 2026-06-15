import json as _json

import pytest
import requests

from reqtor import Response


def _make_response(
    status_code: int = 200,
    json_data: dict | None = None,
    headers: dict | None = None,
) -> Response:
    raw = requests.Response()
    raw.status_code = status_code
    if json_data is not None:
        raw._content = _json.dumps(json_data).encode()
    else:
        raw._content = b""
    raw.headers["content-type"] = (
        "application/json" if json_data is not None else "text/plain"
    )
    if headers:
        raw.headers.update(headers)
    return Response(raw)


class TestResponseProperties:
    def test_status_code(self):
        resp = _make_response(404)
        assert resp.status_code == 404

    def test_ok_true(self):
        resp = _make_response(200)
        assert resp.ok is True

    def test_ok_false(self):
        resp = _make_response(500)
        assert resp.ok is False

    def test_repr(self):
        resp = _make_response(201)
        assert repr(resp) == "Response(status=201)"

    def test_raw_accessible(self):
        raw = requests.Response()
        raw.status_code = 200
        resp = Response(raw)
        assert resp.raw is raw


class TestExpectStatus:
    def test_expect_matching(self):
        resp = _make_response(200)
        result = resp.expect(200)
        assert result is resp

    def test_expect_mismatch(self):
        resp = _make_response(404)
        with pytest.raises(
            AssertionError, match="Expected status 200, got 404"
        ):
            resp.expect(200)


class TestExpectJson:
    def test_expect_json_subset_match(self):
        resp = _make_response(200, json_data={"name": "John", "age": 30})
        resp.expect_json({"name": "John"})

    def test_expect_json_full_match(self):
        resp = _make_response(200, json_data={"name": "John"})
        resp.expect_json({"name": "John"})

    def test_expect_json_missing_key(self):
        resp = _make_response(200, json_data={"name": "John"})
        with pytest.raises(AssertionError, match="Missing key 'email'"):
            resp.expect_json({"email": "test@test.com"})

    def test_expect_json_wrong_value(self):
        resp = _make_response(200, json_data={"name": "John"})
        with pytest.raises(
            AssertionError, match="expected 'Jane', got 'John'"
        ):
            resp.expect_json({"name": "Jane"})


class TestExpectJsonContains:
    def test_expect_json_contains_passes(self):
        resp = _make_response(200, json_data={"name": "John", "age": 30})
        resp.expect_json_contains("name", "age")

    def test_expect_json_contains_fails(self):
        resp = _make_response(200, json_data={"name": "John"})
        with pytest.raises(AssertionError, match="Missing key 'email'"):
            resp.expect_json_contains("email")


class TestExpectHeader:
    def test_expect_header_exists(self):
        resp = _make_response(200, headers={"X-Custom": "val"})
        resp.expect_header("X-Custom")

    def test_expect_header_case_insensitive(self):
        resp = _make_response(
            200, headers={"Content-Type": "application/json"}
        )
        resp.expect_header("content-type")

    def test_expect_header_with_value(self):
        resp = _make_response(200, headers={"X-Custom": "val"})
        resp.expect_header("X-Custom", "val")

    def test_expect_header_missing(self):
        resp = _make_response(200)
        with pytest.raises(AssertionError, match="Missing header"):
            resp.expect_header("X-Missing")

    def test_expect_header_wrong_value(self):
        resp = _make_response(200, headers={"X-Custom": "val"})
        with pytest.raises(
            AssertionError, match="expected 'other', got 'val'"
        ):
            resp.expect_header("X-Custom", "other")


class TestExpectBody:
    def test_expect_body_match(self):
        resp = _make_response(200)
        resp.raw._content = b"hello"
        resp.expect_body("hello")

    def test_expect_body_mismatch(self):
        resp = _make_response(200)
        resp.raw._content = b"hello"
        with pytest.raises(
            AssertionError, match="Expected body 'world', got 'hello'"
        ):
            resp.expect_body("world")


class TestFluentChaining:
    def test_chaining(self):
        resp = _make_response(
            200, json_data={"name": "John"}, headers={"X-Test": "yes"}
        )
        result = (
            resp.expect(200)
            .expect_json({"name": "John"})
            .expect_header("X-Test", "yes")
        )
        assert result is resp
