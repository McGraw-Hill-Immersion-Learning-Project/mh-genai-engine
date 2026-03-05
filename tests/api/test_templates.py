"""Tests for GET /templates and absence of removed support endpoints."""

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


class TestTemplatesEndpoint:
    def test_returns_200(self) -> None:
        resp = client.get("/templates")
        assert resp.status_code == 200

    def test_response_shape_matches_template_list(self) -> None:
        resp = client.get("/templates")
        data = resp.json()

        assert "templates" in data
        assert isinstance(data["templates"], list)
        assert len(data["templates"]) > 0

        first = data["templates"][0]
        for field in ("id", "name", "description"):
            assert field in first
            assert isinstance(first[field], str)


class TestRemovedSupportEndpoints:
    def test_post_retrieve_is_not_exposed(self) -> None:
        resp = client.post("/retrieve", json={"query": "test"})
        assert resp.status_code == 404

    def test_post_telemetry_log_is_not_exposed(self) -> None:
        resp = client.post("/telemetry/log", json={"eventType": "generate"})
        assert resp.status_code == 404

