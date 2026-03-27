"""Tests for POST /generate/lesson-outline and POST /generate/assessment-transform."""

from fastapi.testclient import TestClient

from app.core.rag.retriever import Retriever
from app.deps import get_llm, get_retriever
from app.main import app
from tests.mocks import (
    FakeEmbeddingProvider,
    FakeLLMProvider,
    RefinementDistinctFakeLLMProvider,
    seed_default_lesson_outline_store,
)


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
        assert "chunkId" in citation
        assert citation["chunkId"] == "ap.pdf_0"
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

    def test_chapter_may_be_omitted(self, client: TestClient) -> None:
        body = {k: v for k, v in VALID_LESSON_BODY.items() if k != "chapter"}
        resp = client.post("/generate/lesson-outline", json=body)
        assert resp.status_code == 200

    def test_template_default_accepted(self, client: TestClient) -> None:
        body = {**VALID_LESSON_BODY, "template": "default"}
        resp = client.post("/generate/lesson-outline", json=body)
        assert resp.status_code == 200

    def test_template_lecture_scaffold_one_shot_accepted(self, client: TestClient) -> None:
        body = {**VALID_LESSON_BODY, "template": "lecture-scaffold-one-shot"}
        resp = client.post("/generate/lesson-outline", json=body)
        assert resp.status_code == 200

    def test_rejects_unknown_template(self, client: TestClient) -> None:
        body = {**VALID_LESSON_BODY, "template": "not-a-real-template"}
        resp = client.post("/generate/lesson-outline", json=body)
        assert resp.status_code == 422

    def test_returns_502_when_llm_returns_invalid_json(self) -> None:
        store = seed_default_lesson_outline_store()
        embedder = FakeEmbeddingProvider(dimensions=8)
        app.dependency_overrides[get_retriever] = lambda: Retriever(embedder, store)
        app.dependency_overrides[get_llm] = lambda: FakeLLMProvider("not valid json {{{")
        try:
            with TestClient(app) as c:
                resp = c.post("/generate/lesson-outline", json=VALID_LESSON_BODY)
            assert resp.status_code == 502
            assert "Lesson outline generation failed" in resp.json()["detail"]
        finally:
            app.dependency_overrides.clear()


VALID_REGENERATE_BODY = {
    "previousOutline": {
        "outline": "I. Intro\nII. Body\nIII. Close",
    },
    "refinementInstructions": "Add a 5-minute warm-up at the start.",
}

class TestLessonOutlineRegenerate:
    def test_returns_200(self, client: TestClient) -> None:
        resp = client.post(
            "/generate/lesson-outline/regenerate",
            json=VALID_REGENERATE_BODY,
        )
        assert resp.status_code == 200

    def test_response_matches_lesson_outline_shape(self, client: TestClient) -> None:
        data = client.post(
            "/generate/lesson-outline/regenerate",
            json=VALID_REGENERATE_BODY,
        ).json()
        assert "outline" in data and "citations" in data
        assert isinstance(data["citations"], list)
        assert data["citations"] and "chunkId" in data["citations"][0]

    def test_regenerate_with_chunk_ids_from_prior_citations(self) -> None:
        store = seed_default_lesson_outline_store()
        embedder = FakeEmbeddingProvider(dimensions=8)
        llm = RefinementDistinctFakeLLMProvider()
        app.dependency_overrides[get_retriever] = lambda: Retriever(embedder, store)
        app.dependency_overrides[get_llm] = lambda: llm
        try:
            with TestClient(app) as c:
                gen = c.post("/generate/lesson-outline", json=VALID_LESSON_BODY).json()
                cid = gen["citations"][0]["chunkId"]
                reg = c.post(
                    "/generate/lesson-outline/regenerate",
                    json={
                        "previousOutline": {"outline": gen["outline"]},
                        "refinementInstructions": "Add a warm-up.",
                        "chunkIds": [cid],
                    },
                )
            assert reg.status_code == 200
            data = reg.json()
            assert data["citations"][0]["chunkId"] == cid
        finally:
            app.dependency_overrides.clear()

    def test_regenerate_stale_chunk_ids_returns_422(self) -> None:
        store = seed_default_lesson_outline_store()
        embedder = FakeEmbeddingProvider(dimensions=8)
        llm = RefinementDistinctFakeLLMProvider()
        app.dependency_overrides[get_retriever] = lambda: Retriever(embedder, store)
        app.dependency_overrides[get_llm] = lambda: llm
        try:
            with TestClient(app) as c:
                resp = c.post(
                    "/generate/lesson-outline/regenerate",
                    json={
                        "previousOutline": {"outline": "I. A\nII. B"},
                        "refinementInstructions": "x",
                        "chunkIds": ["does-not-exist"],
                    },
                )
            assert resp.status_code == 422
        finally:
            app.dependency_overrides.clear()

    def test_rejects_missing_previous_outline(self, client: TestClient) -> None:
        body = {k: v for k, v in VALID_REGENERATE_BODY.items() if k != "previousOutline"}
        resp = client.post("/generate/lesson-outline/regenerate", json=body)
        assert resp.status_code == 422

    def test_rejects_missing_refinement_instructions(self, client: TestClient) -> None:
        body = {k: v for k, v in VALID_REGENERATE_BODY.items() if k != "refinementInstructions"}
        resp = client.post("/generate/lesson-outline/regenerate", json=body)
        assert resp.status_code == 422

    def test_minimal_body_only_previous_and_instructions(self, client: TestClient) -> None:
        resp = client.post(
            "/generate/lesson-outline/regenerate",
            json={
                "previousOutline": {"outline": "x"},
                "refinementInstructions": "y",
            },
        )
        assert resp.status_code == 200

    def test_refinement_produces_different_outline_than_generate(self) -> None:
        store = seed_default_lesson_outline_store()
        embedder = FakeEmbeddingProvider(dimensions=8)
        llm = RefinementDistinctFakeLLMProvider()
        app.dependency_overrides[get_retriever] = lambda: Retriever(embedder, store)
        app.dependency_overrides[get_llm] = lambda: llm
        try:
            with TestClient(app) as c:
                gen_data = c.post("/generate/lesson-outline", json=VALID_LESSON_BODY).json()
                reg_data = c.post(
                    "/generate/lesson-outline/regenerate",
                    json={
                        "previousOutline": {"outline": gen_data["outline"]},
                        "refinementInstructions": "Add a warm-up.",
                    },
                ).json()
            assert gen_data["outline"] != reg_data["outline"]
            assert reg_data["outline"].startswith("REFINED:")
        finally:
            app.dependency_overrides.clear()

    def test_returns_502_when_llm_returns_invalid_json(self) -> None:
        store = seed_default_lesson_outline_store()
        embedder = FakeEmbeddingProvider(dimensions=8)
        app.dependency_overrides[get_retriever] = lambda: Retriever(embedder, store)
        app.dependency_overrides[get_llm] = lambda: FakeLLMProvider("not valid json {{{")
        try:
            with TestClient(app) as c:
                resp = c.post(
                    "/generate/lesson-outline/regenerate",
                    json=VALID_REGENERATE_BODY,
                )
            assert resp.status_code == 502
            assert "Lesson outline regeneration failed" in resp.json()["detail"]
        finally:
            app.dependency_overrides.clear()


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
        assert citation.get("chunkId") == "mock_0"
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
