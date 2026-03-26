"""Tests for GET /templates/{workflow}."""

from fastapi.testclient import TestClient


class TestTemplatesByWorkflow:
    def test_lesson_outline_returns_200(self, client: TestClient) -> None:
        resp = client.get("/templates/lesson-outline")
        assert resp.status_code == 200

    def test_lesson_outline_lists_kebab_case_ids(self, client: TestClient) -> None:
        data = client.get("/templates/lesson-outline").json()
        assert "templates" in data
        ids = {t["id"] for t in data["templates"]}
        assert ids == {"default", "lecture-scaffold-one-shot"}

    def test_assessment_transform_returns_200(self, client: TestClient) -> None:
        resp = client.get("/templates/assessment-transform")
        assert resp.status_code == 200

    def test_assessment_transform_includes_default_template(self, client: TestClient) -> None:
        data = client.get("/templates/assessment-transform").json()
        assert len(data["templates"]) == 1
        assert data["templates"][0]["id"] == "default"

    def test_response_shape(self, client: TestClient) -> None:
        data = client.get("/templates/lesson-outline").json()
        for t in data["templates"]:
            for field in ("id", "name", "description"):
                assert field in t
                assert isinstance(t[field], str)

    def test_unknown_workflow_returns_422(self, client: TestClient) -> None:
        resp = client.get("/templates/unknown-workflow")
        assert resp.status_code == 422
