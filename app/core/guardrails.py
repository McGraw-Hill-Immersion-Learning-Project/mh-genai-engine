"""Baseline guardrails v0: prompt injection, harmful content, and out-of-scope detection.

Checks run against the ``learning_objective`` field before the RAG pipeline
executes. Three categories are caught:

1. **Prompt injection** — attempts to override system instructions.
2. **Harmful content** — requests for dangerous or illegal material.
3. **Out-of-scope** — clearly non-educational topics unrelated to course content.

Known limitations: see docs/guardrails-limitations.md.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum


class RefusalReason(str, Enum):
    PROMPT_INJECTION = "prompt_injection"
    HARMFUL_CONTENT = "harmful_content"
    OUT_OF_SCOPE = "out_of_scope"


@dataclass(frozen=True)
class GuardrailResult:
    allowed: bool
    reason: RefusalReason | None = None
    message: str = ""


_INJECTION_PATTERNS: list[str] = [
    # Classic instruction override
    r"ignore\s+(all\s+)?(previous|prior|above|earlier)\s+(instructions?|prompts?|rules?|context)",
    r"disregard\s+(all\s+)?(previous|prior|above|earlier)\s+(instructions?|prompts?|rules?|context)",
    r"forget\s+(all\s+)?(previous|prior|above|earlier)\s+(instructions?|prompts?|rules?|context)",
    # Role-jacking (exclude legitimate educator/student roles)
    r"you\s+are\s+now\s+(a\s+|an\s+)?(?!student|teacher|instructor|tutor|educator|assistant|ai)",
    # System-prompt probing
    r"(print|repeat|output|reveal|show|display)\s+(your\s+)?(system\s+prompt|instructions|rules|configuration)",
    r"(override|bypass|circumvent)\s+(the\s+)?(system|safety|guardrail|filter|restriction)",
    # Markup injection
    r"<\s*/?\s*system\s*>",
    r"\[\s*system\s*\]",
    r"###\s*system",
    r"new\s+(system\s+)?prompt\s*[:\-]",
    # DAN / jailbreak phrasing
    r"\bdo\s+anything\s+now\b",
    r"\bdan\s+mode\b",
    r"\bjailbreak\b",
]

_HARMFUL_PATTERNS: list[str] = [
    r"\b(how\s+to\s+)?(make|create|build|synthesize|produce)\s+(a\s+)?(\w+\s+)?(bomb|explosive|poison|nerve\s+agent|bioweapon)",
    r"\b(suicide|self.?harm|self.?injur)",
    r"\bhow\s+to\s+hack\s+into\b",
    r"\bchild\s+(sexual|pornograph|grooming|abuse)\b",
    r"\b(kill|murder|assassinate|attack)\s+(a\s+)?(person|human|someone|people|individual)",
    r"\b(illegal\s+drug|methamphetamine|heroin|fentanyl)\s+(recipe|synthesis|production|manufacture)",
]

_OUT_OF_SCOPE_PATTERNS: list[str] = [
    # Creative writing / entertainment
    r"^(write|generate|create|compose)\s+(me\s+)?(a\s+)?(poem|short\s+story|novel|song|lyrics|screenplay|joke)",
    # Weather / news / real-time data
    r"(what\s+('s|is)\s+)?(the\s+)?weather\s+(in|for|today|tomorrow)",
    r"(latest|breaking|today'?s?)\s+news",
    # Cooking
    r"(recipe|cooking\s+instructions?)\s+for\b",
    # Financial / trading signals
    r"\b(stock\s+price|cryptocurrency|bitcoin|ethereum|forex|trading\s+signal)",
    # Sports scores
    r"\bwho\s+won\s+the\s+(game|match|championship|tournament)\b",
    r"\b(nfl|nba|mlb|nhl|fifa|premier\s+league)\s+(score|result|standing)",
    # Software implementation requests unrelated to pedagogy
    r"^(write|implement|code)\s+(a\s+)?(python|javascript|typescript|java|c\+\+|sql|bash)\s+(script|program|function|class|query|snippet)\s+that",
]


class Guardrails:
    """Pre-LLM request filter. Instantiate once and call :meth:`check` per request."""

    _injection = [re.compile(p, re.IGNORECASE | re.DOTALL) for p in _INJECTION_PATTERNS]
    _harmful = [re.compile(p, re.IGNORECASE | re.DOTALL) for p in _HARMFUL_PATTERNS]
    _out_of_scope = [re.compile(p, re.IGNORECASE | re.DOTALL) for p in _OUT_OF_SCOPE_PATTERNS]

    def check(self, learning_objective: str) -> GuardrailResult:
        """Return :class:`GuardrailResult` indicating whether the request is allowed.

        Checks are evaluated in priority order:
        injection → harmful → out-of-scope.
        The first match short-circuits remaining checks.
        """
        text = (learning_objective or "").strip()

        for pattern in self._injection:
            if pattern.search(text):
                return GuardrailResult(
                    allowed=False,
                    reason=RefusalReason.PROMPT_INJECTION,
                    message=(
                        "This request contains patterns that are not permitted. "
                        "Please provide a learning objective related to your course material."
                    ),
                )

        for pattern in self._harmful:
            if pattern.search(text):
                return GuardrailResult(
                    allowed=False,
                    reason=RefusalReason.HARMFUL_CONTENT,
                    message=(
                        "This request cannot be fulfilled. "
                        "Please provide a learning objective related to your course material."
                    ),
                )

        for pattern in self._out_of_scope:
            if pattern.search(text):
                return GuardrailResult(
                    allowed=False,
                    reason=RefusalReason.OUT_OF_SCOPE,
                    message=(
                        "This request is outside the scope of course content generation. "
                        "Please provide a learning objective related to your course material."
                    ),
                )

        return GuardrailResult(allowed=True)


# Module-level singleton — shared across requests (patterns are compiled once).
guardrails = Guardrails()
