## Shared constraints

- Honor **audience level** and **learning objective**.
- Use **only** the retrieved passages in the **task template** (below) for factual claims, per that template’s grounding rules.
- Return **only** the JSON object the template specifies, with **exact** field names.
- For **`outline`**, **`slideOutline`**, and the meaning of **`count`**, follow the **Format** section in this block; if the task template disagrees on those points, **this block wins**. Grounding tag syntax in the task template still applies.

## Format: `lecture_notes` (this request)

You are producing a **time-based lesson or lecture plan** for instructor notes or live delivery (flow, segments, transitions; optional rough timing cues).

- **`count`:** **Session length in minutes.** Calibrate depth, number of checks/activities, and segment granularity to fit roughly that duration.
- **`outline`:** **Primary deliverable** — ordered, **lesson-ready** structure grounded in retrieved passages. Optimize for **spoken or written class flow**, not slide choreography.
- **`slideOutline`:** JSON value must be **`null`**. Do not emit slide lists.

Ignore any instructions elsewhere that describe slide decks or `slideOutline` body text; they do not apply to this request.
