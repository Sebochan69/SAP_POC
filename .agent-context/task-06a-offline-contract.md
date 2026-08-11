# Feature 6A — Offline integration contract and confirmation gate

## Owner

OMP implements this safe first slice. Pi reviews it. No live SAP/Edge action is authorized yet because the Feature 5 questions about the approved environment, selectors, session, and side effects remain unanswered.

## Context

Features 1–5 are approved and preserved in `.agent-context/task-01-leave-preview.md` through `.agent-context/task-05-integration-plan.md`. Read `docs/INTEGRATION_PLAN.md` and `AGENTS.md` before coding.

## Goal

Implement only the offline contract between the deterministic dry-run preview and a future browser adapter. This locks the preview/confirmation boundary without launching Edge, connecting to SAP, handling credentials, or submitting anything.

## Required boundary

- Do not edit the browser/SAP plan into an implementation.
- Do not launch Edge, connect to SAP, add browser dependencies, read credentials, make network calls, add SAP URLs/selectors, or add a submission route.
- Keep `POST /api/preview` unchanged and keep `python3 verify.py` deterministic.
- Leave the existing dry-run planner as the only source of planned rows; do not reinterpret raw user text.

## Offline contract

Add the smallest standard-library-only module needed (for example `integration_contract.py`) with deterministic functions that:

1. Accept a validated preview object only when `kind == "preview"`, there are no clarifications, and at least one planned leave/work row exists.
2. Produce a canonical adapter plan containing:
   - a stable SHA-256 `plan_id` over canonical JSON;
   - `state: "previewed"`;
   - `requires_confirmation: true`;
   - normalized planned rows (leave or work) with dates and already validated fields;
   - safe monthly/skip summaries and the existing dry-run warning;
   - no raw user text, model output, credentials, cookies, tokens, or arbitrary page text.
3. Provide a deterministic confirmation function that accepts a plan and its exact `plan_id` and returns an `awaiting_confirmation` result only when the hash still matches. A changed plan must fail closed.
4. Define/validate only offline states needed now: `previewed`, `awaiting_confirmation`, and `failed`. Do not produce `checked` or `submitted`; those require a future live adapter and separate gate evidence.
5. Reject malformed previews, unresolved clarifications, empty plans, changed rows, unknown request kinds, and unsupported arbitrary fields rather than guessing.

The contract is an internal handoff/test seam, not a new HTTP endpoint. Do not put plan IDs or preview contents in JSONL logs unless they are safe counts/categories; never log WBS codes, descriptions, leave dates, or user text.

## Tests / verification

Extend `python3 verify.py` or add a small standard-library test module:

- complete leave and work previews become stable `previewed` adapter plans;
- canonical plan IDs are repeatable and change when a planned row changes;
- exact matching confirmation returns `awaiting_confirmation`; stale/changed IDs fail closed;
- clarification, empty, unknown-kind, malformed, or unsupported plans are rejected;
- output/log checks contain no raw user text, WBS code, task description, credentials, cookies, or tokens;
- all existing 22 tests remain passing and `/api/submit` remains 404.

Run:

```bash
python3 verify.py
python3 -m py_compile app.py verify.py integration_contract.py
```

No live Ollama, network, SAP, Edge, browser, or visual verification.

## Acceptance criteria

- Offline adapter contract and explicit confirmation gate are tested and documented.
- Current app remains dry-run only and unchanged at the HTTP boundary.
- No live integration or submission behavior is possible from this feature.
- Handoffs/findings/decisions state that live Edge/SAP work still requires answering Feature 5 gates and separate approval for the next slice.

## Result

Pi review blockers are fixed and Feature 6A is approved by Pi review. The offline adapter contract and confirmation gate are covered by 33 deterministic tests; `app.py` and its HTTP routes remain unchanged. No live Edge/SAP/credential/network/submission behavior or browser verification was used. Feature 6B remains separately gated by the unanswered Feature 5 questions and approval.
