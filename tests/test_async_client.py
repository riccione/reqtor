import httpx
import pytest
import respx

from reqtor import AsyncAPI


class TestAsyncAPIInit:
    def test_base_url_strips_trailing_slash(self):
        api = AsyncAPI("https://example.com/")
        assert api.base_url == "https://example.com"

    def test_base_url_no_trailing_slash(self):
        api = AsyncAPI("https://example.com")
        assert api.base_url == "https://example.com"

    def test_repr(self):
        api = AsyncAPI("https://example.com")
        assert repr(api) == "AsyncAPI(base_url='https://example.com')"

    def test_client_has_token_header(self):
        api = AsyncAPI("https://example.com", token="mytoken")
        assert api.client.headers["Authorization"] == "Bearer mytoken"

    def test_client_has_custom_headers(self):
        api = AsyncAPI("https://example.com", headers={"X-Custom": "value"})
        assert api.client.headers["X-Custom"] == "value"


class TestAsyncAPIMethods:
    @respx.mock
    @pytest.mark.asyncio
    async def test_request_returns_response(self):
        respx.get("https://example.com/get").mock(
            return_value=httpx.Response(200, json={})
        )
        async with AsyncAPI("https://example.com") as api:
            resp = await api.request("GET", "/get")
            assert resp.status_code == 200

    @respx.mock
    @pytest.mark.asyncio
    async def test_get(self):
        respx.get("https://example.com/get").mock(
            return_value=httpx.Response(200, json={})
        )
        async with AsyncAPI("https://example.com") as api:
            resp = await api.get("/get")
            assert resp.status_code == 200

    @respx.mock
    @pytest.mark.asyncio
    async def test_post(self):
        respx.post("https://example.com/post").mock(
            return_value=httpx.Response(200, json={"json": {"key": "value"}})
        )
        async with AsyncAPI("https://example.com") as api:
            resp = await api.post("/post", json={"key": "value"})
            assert resp.status_code == 200
            assert resp.json["json"] == {"key": "value"}

    @respx.mock
    @pytest.mark.asyncio
    async def test_put(self):
        respx.put("https://example.com/put").mock(
            return_value=httpx.Response(200, json={})
        )
        async with AsyncAPI("https://example.com") as api:
            resp = await api.put("/put", json={"key": "value"})
            assert resp.status_code == 200

    @respx.mock
    @pytest.mark.asyncio
    async def test_patch(self):
        respx.patch("https://example.com/patch").mock(
            return_value=httpx.Response(200, json={})
        )
        async with AsyncAPI("https://example.com") as api:
            resp = await api.patch("/patch", json={"key": "value"})
            assert resp.status_code == 200

    @respx.mock
    @pytest.mark.asyncio
    async def test_delete(self):
        respx.delete("https://example.com/delete").mock(
            return_value=httpx.Response(200)
        )
        async with AsyncAPI("https://example.com") as api:
            resp = await api.delete("/delete")
            assert resp.status_code == 200

    @respx.mock
    @pytest.mark.asyncio
    async def test_head(self):
        respx.head("https://example.com/get").mock(
            return_value=httpx.Response(200)
        )
        async with AsyncAPI("https://example.com") as api:
            resp = await api.head("/get")
            assert resp.status_code == 200

    @respx.mock
    @pytest.mark.asyncio
    async def test_options(self):
        respx.options("https://example.com/get").mock(
            return_value=httpx.Response(200)
        )
        async with AsyncAPI("https://example.com") as api:
            resp = await api.options("/get")
            assert resp.status_code == 200


class TestAsyncAPIAuth:
    @respx.mock
    @pytest.mark.asyncio
    async def test_api_key_in_params(self):
        respx.get("https://example.com/data").mock(
            return_value=httpx.Response(200, json={})
        )
        async with AsyncAPI("https://example.com", api_key="secret123") as api:
            resp = await api.get("/data")
            assert resp.status_code == 200

    @respx.mock
    @pytest.mark.asyncio
    async def test_api_key_custom_param(self):
        respx.get("https://example.com/data").mock(
            return_value=httpx.Response(200, json={})
        )
        async with AsyncAPI(
            "https://example.com",
            api_key="key123",
            api_key_param="access_token",
        ) as api:
            resp = await api.get("/data")
            assert resp.status_code == 200


class TestAsyncAPIContextManager:
    @respx.mock
    @pytest.mark.asyncio
    async def test_context_manager(self):
        respx.get("https://example.com/get").mock(
            return_value=httpx.Response(200, json={})
        )
        async with AsyncAPI("https://example.com") as api:
            resp = await api.get("/get")
            assert resp.status_code == 200


class TestAsyncAPIHooks:
    @respx.mock
    @pytest.mark.asyncio
    async def test_before_hook(self):
        captured = {}

        def before(kwargs):
            captured.update(kwargs)

        respx.get("https://example.com/data").mock(
            return_value=httpx.Response(200, json={})
        )
        async with AsyncAPI(
            "https://example.com",
            hooks={"before": before},
        ) as api:
            await api.get("/data")
        assert captured["method"] == "GET"
        assert "/data" in str(captured["url"])

    @respx.mock
    @pytest.mark.asyncio
    async def test_after_hook(self):
        captured = {}

        def after(resp):
            captured["status"] = resp.status_code

        respx.get("https://example.com/data").mock(
            return_value=httpx.Response(200, json={})
        )
        async with AsyncAPI(
            "https://example.com",
            hooks={"after": after},
        ) as api:
            await api.get("/data")
        assert captured["status"] == 200


class TestAsyncAPIDebug:
    @respx.mock
    @pytest.mark.asyncio
    async def test_debug_prints_to_stderr(self, capsys):
        respx.get("https://example.com/data").mock(
            return_value=httpx.Response(200, json={})
        )
        async with AsyncAPI("https://example.com", debug=True) as api:
            await api.get("/data")
        captured = capsys.readouterr()
        assert "[reqtor]" in captured.err
        assert "200" in captured.err


class TestAsyncLazyImport:
    def test_async_api_lazy_import(self):
        from reqtor import AsyncAPI as LazyAsyncAPI

        assert LazyAsyncAPI is not None

    def test_async_response_lazy_import(self):
        from reqtor import AsyncResponse as LazyAsyncResponse

        assert LazyAsyncResponse is not None

    def test_invalid_attribute_raises(self):
        import reqtor

        with pytest.raises(AttributeError):
            _ = reqtor.NonExistent
