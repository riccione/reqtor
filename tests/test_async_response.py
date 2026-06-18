import httpx
import pytest

from reqtor.async_response import AsyncResponse


def _make_async_response(
    status_code: int = 200,
    json_data: dict | None = None,
    headers: dict | None = None,
    content: bytes | None = None,
) -> AsyncResponse:
    if json_data is not None:
        raw = httpx.Response(
            status_code,
            json=json_data,
            headers=headers or {},
        )
    elif content is not None:
        raw = httpx.Response(
            status_code,
            content=content,
            headers=headers or {},
        )
    else:
        raw = httpx.Response(
            status_code,
            content=b"",
            headers=headers or {},
        )
    return AsyncResponse(raw)


class TestAsyncResponseProperties:
    def test_status_code(self):
        resp = _make_async_response(404)
        assert resp.status_code == 404

    def test_ok_true(self):
        resp = _make_async_response(200)
        assert resp.ok is True

    def test_ok_false(self):
        resp = _make_async_response(500)
        assert resp.ok is False

    def test_repr(self):
        resp = _make_async_response(201)
        assert repr(resp) == "AsyncResponse(status=201)"

    def test_raw_accessible(self):
        raw = httpx.Response(200)
        resp = AsyncResponse(raw)
        assert resp.raw is raw

    def test_text(self):
        resp = _make_async_response(200, content=b"hello")
        assert resp.text == "hello"

    def test_content(self):
        resp = _make_async_response(200, content=b"hello")
        assert resp.content == b"hello"

    def test_json_property(self):
        resp = _make_async_response(200, json_data={"key": "value"})
        assert resp.json == {"key": "value"}


class TestAsyncExpectStatus:
    def test_expect_matching(self):
        resp = _make_async_response(200)
        result = resp.expect(200)
        assert result is resp

    def test_expect_mismatch(self):
        resp = _make_async_response(404)
        with pytest.raises(
            AssertionError, match="Expected status 200, got 404"
        ):
            resp.expect(200)


class TestAsyncExpectOk:
    def test_expect_ok_passes(self):
        for status in (200, 201, 204, 299):
            resp = _make_async_response(status)
            resp.expect_ok()

    def test_expect_ok_fails(self):
        resp = _make_async_response(404)
        with pytest.raises(AssertionError, match="Expected 2xx"):
            resp.expect_ok()


class TestAsyncExpectJson:
    def test_expect_json_subset_match(self):
        resp = _make_async_response(200, json_data={"name": "John", "age": 30})
        resp.expect_json({"name": "John"})

    def test_expect_json_nested_path(self):
        resp = _make_async_response(200, json_data={"user": {"name": "John"}})
        resp.expect_json({"user.name": "John"})

    def test_expect_json_wrong_value(self):
        resp = _make_async_response(200, json_data={"name": "John"})
        with pytest.raises(
            AssertionError, match="expected 'Jane', got 'John'"
        ):
            resp.expect_json({"name": "Jane"})


class TestAsyncExpectJsonContains:
    def test_expect_json_contains_passes(self):
        resp = _make_async_response(200, json_data={"name": "John", "age": 30})
        resp.expect_json_contains("name", "age")

    def test_expect_json_contains_nested(self):
        resp = _make_async_response(200, json_data={"user": {"name": "John"}})
        resp.expect_json_contains("user.name")

    def test_expect_json_contains_fails(self):
        resp = _make_async_response(200, json_data={"name": "John"})
        with pytest.raises(AssertionError, match="Missing key"):
            resp.expect_json_contains("email")


class TestAsyncExpectJsonLength:
    def test_expect_json_length_passes(self):
        resp = _make_async_response(200, json_data={"items": [1, 2, 3]})
        resp.expect_json_length("items", 3)

    def test_expect_json_length_wrong(self):
        resp = _make_async_response(200, json_data={"items": [1, 2]})
        with pytest.raises(AssertionError, match="expected length 3, got 2"):
            resp.expect_json_length("items", 3)

    def test_expect_json_length_not_list(self):
        resp = _make_async_response(200, json_data={"items": "not"})
        with pytest.raises(AssertionError, match="expected list"):
            resp.expect_json_length("items", 1)


class TestAsyncExpectJsonType:
    def test_expect_json_type_passes(self):
        resp = _make_async_response(200, json_data={"name": "John", "age": 30})
        resp.expect_json_type("name", str)
        resp.expect_json_type("age", int)

    def test_expect_json_type_wrong(self):
        resp = _make_async_response(200, json_data={"name": "John"})
        with pytest.raises(AssertionError, match="expected int.*got str"):
            resp.expect_json_type("name", int)


class TestAsyncExpectHeader:
    def test_expect_header_exists(self):
        resp = _make_async_response(200, headers={"X-Custom": "val"})
        resp.expect_header("X-Custom")

    def test_expect_header_with_value(self):
        resp = _make_async_response(200, headers={"X-Custom": "val"})
        resp.expect_header("X-Custom", "val")

    def test_expect_header_missing(self):
        resp = _make_async_response(200)
        with pytest.raises(AssertionError, match="Missing header"):
            resp.expect_header("X-Missing")

    def test_expect_header_wrong_value(self):
        resp = _make_async_response(200, headers={"X-Custom": "val"})
        with pytest.raises(
            AssertionError, match="expected 'other', got 'val'"
        ):
            resp.expect_header("X-Custom", "other")


class TestAsyncExpectNoHeader:
    def test_expect_no_header_passes(self):
        resp = _make_async_response(200)
        resp.expect_no_header("X-Missing")

    def test_expect_no_header_fails(self):
        resp = _make_async_response(200, headers={"X-Exists": "yes"})
        with pytest.raises(AssertionError, match="Unexpected header"):
            resp.expect_no_header("X-Exists")


class TestAsyncExpectBody:
    def test_expect_body_match(self):
        resp = _make_async_response(200, content=b"hello")
        resp.expect_body("hello")

    def test_expect_body_mismatch(self):
        resp = _make_async_response(200, content=b"hello")
        with pytest.raises(AssertionError, match="Expected body 'world'"):
            resp.expect_body("world")


class TestAsyncExpectBodyContains:
    def test_expect_body_contains_passes(self):
        resp = _make_async_response(200, content=b"hello world")
        resp.expect_body_contains("world")

    def test_expect_body_contains_fails(self):
        resp = _make_async_response(200, content=b"hello")
        with pytest.raises(AssertionError, match="Expected body to contain"):
            resp.expect_body_contains("world")


class TestAsyncExpectBodyMatches:
    def test_expect_body_matches_passes(self):
        resp = _make_async_response(200, content=b"error: 42 not found")
        resp.expect_body_matches(r"\d+")

    def test_expect_body_matches_fails(self):
        resp = _make_async_response(200, content=b"no numbers here")
        with pytest.raises(AssertionError, match="Expected body to match"):
            resp.expect_body_matches(r"\d+")


class TestAsyncExpectLatency:
    def test_expect_latency_passes(self):
        resp = _make_async_response(200)
        resp._raw.elapsed = __import__("datetime").timedelta(seconds=0.5)
        resp.expect_latency(10.0)

    def test_expect_latency_fails(self):
        resp = _make_async_response(200)
        resp._raw.elapsed = __import__("datetime").timedelta(seconds=5.0)
        with pytest.raises(AssertionError, match="Expected latency"):
            resp.expect_latency(1.0)


class TestAsyncFluentChaining:
    def test_chaining(self):
        resp = _make_async_response(
            200,
            json_data={"name": "John"},
            headers={"X-Test": "yes"},
        )
        result = (
            resp.expect(200)
            .expect_json({"name": "John"})
            .expect_header("X-Test", "yes")
        )
        assert result is resp
