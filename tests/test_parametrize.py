import responses

from reqtor import API, api_endpoints, endpoints, http_methods, statuses


class TestEndpoints:
    @responses.activate
    def test_endpoints_basic(self):
        responses.add(
            responses.GET, "https://example.com/users", json={}, status=200
        )
        responses.add(
            responses.GET, "https://example.com/posts", json={}, status=200
        )
        responses.add(
            responses.GET, "https://example.com/comments", json={}, status=200
        )

        @endpoints("/users", "/posts", "/comments")
        def test_fn(api, path):
            api.get(path).expect(200)

        api = API("https://example.com")
        test_fn(api, "/users")
        test_fn(api, "/posts")
        test_fn(api, "/comments")

    @responses.activate
    def test_endpoints_with_method(self):
        responses.add(
            responses.POST, "https://example.com/users", json={}, status=201
        )
        responses.add(
            responses.POST, "https://example.com/posts", json={}, status=201
        )

        @endpoints("/users", "/posts", method="POST", status=201)
        def test_fn(api, path):
            api.post(path).expect(201)

        api = API("https://example.com")
        test_fn(api, "/users")
        test_fn(api, "/posts")


class TestStatuses:
    @responses.activate
    def test_statuses_basic(self):
        responses.add(
            responses.GET, "https://example.com/test", json={}, status=200
        )
        responses.add(
            responses.GET, "https://example.com/test", json={}, status=201
        )
        responses.add(responses.GET, "https://example.com/test", status=204)

        @statuses(200, 201, 204)
        def test_fn(api, status):
            api.get("/test").expect(status)

        api = API("https://example.com")
        test_fn(api, 200)
        test_fn(api, 201)
        test_fn(api, 204)


class TestHttpMethods:
    @responses.activate
    def test_http_methods_basic(self):
        responses.add(
            responses.GET, "https://example.com/test", json={}, status=200
        )
        responses.add(
            responses.POST, "https://example.com/test", json={}, status=200
        )
        responses.add(
            responses.PUT, "https://example.com/test", json={}, status=200
        )
        responses.add(
            responses.DELETE, "https://example.com/test", json={}, status=200
        )

        @http_methods("GET", "POST", "PUT", "DELETE")
        def test_fn(api, method):
            resp = getattr(api, method.lower())("/test")
            resp.expect(200)

        api = API("https://example.com")
        test_fn(api, "GET")
        test_fn(api, "POST")
        test_fn(api, "PUT")
        test_fn(api, "DELETE")


class TestApiEndpoints:
    @responses.activate
    def test_api_endpoints_basic(self):
        responses.add(
            responses.GET, "https://example.com/users", json={}, status=200
        )
        responses.add(
            responses.GET, "https://example.com/posts", json={}, status=200
        )
        responses.add(
            responses.GET, "https://example.com/missing", json={}, status=404
        )

        @api_endpoints(("/users", 200), ("/posts", 200), ("/missing", 404))
        def test_fn(api, path, expected_status):
            api.get(path).expect(expected_status)

        api = API("https://example.com")
        test_fn(api, "/users", 200)
        test_fn(api, "/posts", 200)
        test_fn(api, "/missing", 404)

    @responses.activate
    def test_api_endpoints_with_method(self):
        responses.add(
            responses.POST, "https://example.com/users", json={}, status=201
        )
        responses.add(
            responses.POST, "https://example.com/posts", json={}, status=201
        )

        @api_endpoints(("/users", 201), ("/posts", 201), method="POST")
        def test_fn(api, path, expected_status):
            api.post(path).expect(expected_status)

        api = API("https://example.com")
        test_fn(api, "/users", 201)
        test_fn(api, "/posts", 201)


class TestParametrizeIntegration:
    @responses.activate
    def test_combined_with_fixtures(self):
        responses.add(
            responses.GET, "https://example.com/users", json={}, status=200
        )
        responses.add(
            responses.GET, "https://example.com/posts", json={}, status=200
        )

        @endpoints("/users", "/posts")
        def test_get_endpoints(api, path):
            api.get(path).expect(200)

        api = API("https://example.com")
        test_get_endpoints(api, "/users")
        test_get_endpoints(api, "/posts")
