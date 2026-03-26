"""Tests for app.utils helpers."""

from app.utils import normalize_citation_snippet_text


def test_normalize_citation_snippet_text_collapses_whitespace() -> None:
    assert normalize_citation_snippet_text("a\n\nb\tc") == "a b c"


def test_normalize_citation_snippet_text_strips_ascii_controls() -> None:
    raw = "PREDICTIONS\nOF\nSUPPL\x02\x03Y"
    assert normalize_citation_snippet_text(raw) == "PREDICTIONS OF SUPPLY"


def test_normalize_citation_snippet_text_empty() -> None:
    assert normalize_citation_snippet_text("") == ""
