import pytest

from reqtor import API

BASE_URL = "https://catfact.ninja"


@pytest.mark.live
class TestCatFactsAPI:
    def test_get_random_cat_fact(self):
        api = API(BASE_URL)
        resp = api.get("/fact")
        resp.expect(200).expect_json_contains("fact")
        assert isinstance(resp.json["fact"], str)
        assert len(resp.json["fact"]) > 0

    def test_get_multiple_facts(self):
        api = API(BASE_URL)
        resp = api.get("/facts", params={"limit": "3"})
        resp.expect(200).expect_json_contains("data")
        data = resp.json["data"]
        assert isinstance(data, list)
        assert len(data) == 3
        for item in data:
            assert "fact" in item
            assert isinstance(item["fact"], str)

    def test_fluent_chaining(self):
        api = API(BASE_URL)
        (
            api.get("/fact")
            .expect(200)
            .expect_json_contains("fact", "length")
            .expect_header("content-type", "application/json")
        )
