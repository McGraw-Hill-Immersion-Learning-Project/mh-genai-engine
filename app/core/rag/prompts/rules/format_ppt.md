## Shared constraints

- Honor **audience level** and **learning objective**.
- Use **only** the retrieved passages in the **task template** (below) for factual claims, per that template’s grounding rules.
- Return **only** the JSON object the template specifies, with **exact** field names.
- For **`outline`**, **`slideOutline`**, and the meaning of **`count`**, follow the **Format** section in this block; if the task template disagrees on those points, **this block wins**. Grounding tag syntax in the task template still applies.

## Format: `ppt` (this request)

You are producing a plan for a **projected slide deck** the instructor will present.

- **`count`:** **Target number of slides** (approximate). Shape `slideOutline` to roughly match unless the content clearly needs fewer or more slides for coherence.
- **`outline`:** **Supporting** lesson spine, speaker-note cues, or conceptual thread—aligned with the same objective and sources. **Do not** duplicate every slide line-by-line; complement the deck.
- **`slideOutline`:** **Required non-empty string.** **Slide-by-slide plan:** each slide with a **title** and **key bullets** (or short speaker cues). Use clear labels (e.g. `Slide 1: Title`). When a bullet or cue is **directly supported** by a retrieved passage, wrap the supported substring in ``<grounded ref="INDEX">…</grounded>`` (same rules as in the task template)—**not** `[Ref N]` or other shorthand.

Ignore any instructions elsewhere that describe minute-based lesson pacing or `slideOutline: null`; they do not apply to this request.
