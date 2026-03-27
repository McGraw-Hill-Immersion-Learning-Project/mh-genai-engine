# Guardrails Baseline v0 — Known Limitations

This document describes what the v0 guardrails do and do not protect against. It is a required deliverable for Issue #24.

## What the guardrails check

Three categories of input are blocked **before** the RAG pipeline runs:

| Category | Examples caught |
|---|---|
| **Prompt injection** | "ignore previous instructions", "jailbreak", DAN mode, system-prompt probing, XML/markup injection |
| **Harmful content** | Weapon synthesis, self-harm, hacking instructions, child exploitation, controlled-substance recipes |
| **Out-of-scope** | Creative writing (poems, stories), weather queries, cooking recipes, financial signals, sports scores, standalone code-generation requests |

All checks operate on the `learning_objective` field only. Refusals return HTTP 400 with a plain-English `detail` message.

## Known limitations

### 1. Pattern-matching only — no semantic understanding
Guardrails use compiled regular expressions. Paraphrases, synonyms, misspellings, or non-English inputs that carry the same intent may bypass detection.

Example bypass: `"Kindly overlook prior directives"` (synonym for "ignore previous instructions").

### 2. Checks only the `learning_objective` field
`book`, `chapter`, `section`, `sub_section`, and other request fields are not inspected. Injections embedded in those fields would not be caught.

### 3. No post-generation output filter
The LLM response is returned as-is. If the model generates unsafe or off-topic content despite the pre-check, there is no second-pass filter.

### 4. Out-of-scope detection is conservative by design
The out-of-scope rules target clearly non-educational request phrasings (e.g., "write me a poem"). Subtle off-topic objectives that use educational language (e.g., "Explain the history of Bitcoin prices for a finance course") will pass through.

### 5. No rate limiting or abuse-pattern tracking
Guardrails are stateless per-request. Repeated probing, fuzzing, or high-volume abuse is not detected or throttled at this layer.

### 6. Injection via multi-turn context is out of scope
This endpoint is stateless (no conversation history). Multi-turn injection attacks are not applicable but are noted for future chat-based extensions.

### 7. LLM-level injection is not fully mitigated
Prompt injection embedded in **retrieved document chunks** (i.e., injected into the OER source material in the vector DB) is not caught by input guardrails. This requires a separate output-layer or retrieval-layer control.

## Recommendations for v1+

- Add a semantic classifier (e.g., a lightweight Claude call or a fine-tuned classifier) as a second-pass check for injection and harm.
- Extend checks to all string request fields.
- Add a post-generation content filter using Claude's moderation capabilities or a separate safety model.
- Log refusal events with reason codes for monitoring and pattern analysis.
- Consider rate limiting at the API gateway for endpoints with guardrails.
