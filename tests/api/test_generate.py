"""Tests for POST /generate/lesson-outline and POST /generate/assessment-transform."""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


VALID_LESSON_BODY = {
    "chapter": "6",
    "learningObjective": "Describe bone structure",
    "contentType": "lecture_notes",
    "count": 45,
    "audienceLevel": "intermediate",
}

VALID_ASSESSMENT_BODY = {
    "question": "Which cell type is responsible for bone resorption?",
    "options": ["Osteoblast", "Osteoclast", "Osteocyte", "Chondrocyte"],
}


# ── lesson-outline ──────────────────────────────────────────────


class TestLessonOutline:
    def test_returns_200(self, client: TestClient) -> None:
        resp = client.post("/generate/lesson-outline", json=VALID_LESSON_BODY)
        assert resp.status_code == 200

    def test_response_has_required_keys(self, client: TestClient) -> None:
        data = client.post("/generate/lesson-outline", json=VALID_LESSON_BODY).json()
        assert "outline" in data
        assert isinstance(data["outline"], str)
        assert len(data["outline"]) > 0

    def test_response_has_citations_as_objects(self, client: TestClient) -> None:
        data = client.post("/generate/lesson-outline", json=VALID_LESSON_BODY).json()
        assert isinstance(data["citations"], list)
        assert len(data["citations"]) > 0
        citation = data["citations"][0]
        assert "title" in citation
        assert "chapter" in citation

    def test_response_has_optional_list_fields(self, client: TestClient) -> None:
        data = client.post("/generate/lesson-outline", json=VALID_LESSON_BODY).json()
        for field in ("keyConcepts", "misconceptions", "checksForUnderstanding", "activityIdeas"):
            assert isinstance(data[field], list)

    def test_slide_outline_null_for_lecture_notes(self, client: TestClient) -> None:
        data = client.post("/generate/lesson-outline", json=VALID_LESSON_BODY).json()
        assert data["slideOutline"] is None

    def test_slide_outline_populated_for_ppt(self, client: TestClient) -> None:
        body = {**VALID_LESSON_BODY, "contentType": "ppt"}
        data = client.post("/generate/lesson-outline", json=body).json()
        assert isinstance(data["slideOutline"], str)
        assert len(data["slideOutline"]) > 0

    def test_rejects_missing_required_fields(self, client: TestClient) -> None:
        resp = client.post("/generate/lesson-outline", json={})
        assert resp.status_code == 422

    def test_rejects_invalid_content_type(self, client: TestClient) -> None:
        body = {**VALID_LESSON_BODY, "contentType": "video"}
        resp = client.post("/generate/lesson-outline", json=body)
        assert resp.status_code == 422

    def test_rejects_invalid_audience_level(self, client: TestClient) -> None:
        body = {**VALID_LESSON_BODY, "audienceLevel": "expert"}
        resp = client.post("/generate/lesson-outline", json=body)
        assert resp.status_code == 422

    def test_optional_fields_accepted(self, client: TestClient) -> None:
        body = {
            **VALID_LESSON_BODY,
            "book": "Anatomy & Physiology",
            "section": "6.3",
            "subSection": "6.3.1",
            "regeneratedResponse": True,
        }
        resp = client.post("/generate/lesson-outline", json=body)
        assert resp.status_code == 200


# ── assessment-transform ────────────────────────────────────────


class TestAssessmentTransform:
    def test_returns_200(self, client: TestClient) -> None:
        resp = client.post("/generate/assessment-transform", json=VALID_ASSESSMENT_BODY)
        assert resp.status_code == 200

    def test_response_has_required_keys(self, client: TestClient) -> None:
        data = client.post("/generate/assessment-transform", json=VALID_ASSESSMENT_BODY).json()
        for key in ("openEndedQuestion", "rubric", "expectedResponseOutline"):
            assert key in data
            assert isinstance(data[key], str)
            assert len(data[key]) > 0

    def test_response_has_citations_as_objects(self, client: TestClient) -> None:
        data = client.post("/generate/assessment-transform", json=VALID_ASSESSMENT_BODY).json()
        assert isinstance(data["citations"], list)
        assert len(data["citations"]) > 0
        citation = data["citations"][0]
        assert "title" in citation
        assert "chapter" in citation

    def test_response_has_misconceptions(self, client: TestClient) -> None:
        data = client.post("/generate/assessment-transform", json=VALID_ASSESSMENT_BODY).json()
        assert isinstance(data["misconceptions"], list)
        assert len(data["misconceptions"]) > 0

    def test_rejects_missing_question(self, client: TestClient) -> None:
        resp = client.post("/generate/assessment-transform", json={})
        assert resp.status_code == 422

    def test_question_only_is_valid(self, client: TestClient) -> None:
        resp = client.post("/generate/assessment-transform", json={"question": "Why?"})
        assert resp.status_code == 200

    def test_optional_fields_accepted(self, client: TestClient) -> None:
        body = {
            **VALID_ASSESSMENT_BODY,
            "learningObjectives": ["Identify bone cell types"],
        }
        resp = client.post("/generate/assessment-transform", json=body)
        assert resp.status_code == 200
