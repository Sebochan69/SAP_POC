# Feature 6E — Local SAP-like sandbox

## Owner

OMP implements this local-only controlled environment. Pi reviews and approves it. Real Feature 6B SAP/Edge integration remains blocked.

## Purpose

The user has no non-production SAP system. Build a small local SAP-like sandbox so the POC can exercise the future lifecycle safely without pretending to validate real SAP behavior.

## Required boundaries

- Use Python 3.12 standard library only.
- Add a separate executable, preferably `mock_sap_sandbox.py`; do not modify `app.py` routes or enable `/api/submit`.
- Bind the CLI server to `127.0.0.1` only. No outbound network, Ollama, SAP, Edge, browser automation, credentials, cookies, tokens, or external services.
- Use the approved `MockSapAdapter`, `integration_contract.py`, and deterministic in-memory preview/plan helpers. Never write `config/mock_sap_2026.json` or any other state file.
- Every UI/API response must be clearly marked `mock_only: true` or `MOCK ONLY`; never call the result SAP behavior or real submission.
- In-memory state may reset on process restart or an explicit reset endpoint. No persistence is needed.

## Minimum sandbox behavior

Serve a visibly labeled local HTML page and JSON API:

- `GET /` — mock-only UI with scenario selector and lifecycle buttons.
- `GET /api/mock/state` — discovery, redacted existing entries, and monthly status.
- `GET /api/mock/plan?scenario=safe|duplicate|locked|released` — deterministic one-row plan wrapped in mock-only metadata.
- `POST /api/mock/check` — accept a validated previewed plan and call `MockSapAdapter.check_row()`.
- `POST /api/mock/confirm` — call exact `confirm_adapter_plan()` with the supplied plan ID.
- `POST /api/mock/update` — accept the exact plan plus awaiting confirmation and call `update_one_row()`.
- `POST /api/mock/reset` — reset the in-memory adapter only.
- Unknown routes, including `/api/submit`, remain 404.

Scenarios use existing fixture rows/statuses:

- `safe`: July 15, 2026 sickness; check and one-row mock update succeed.
- `duplicate`: July 16, 2026; Check fails closed with `duplicate`.
- `locked`: August 17, 2026; Check fails closed with `locked`.
- `released`: September 1, 2026; Check fails closed with `released`.

The page must show the plan and returned state/error JSON without requiring Ollama. The safe flow must visibly support:
`previewed -> mock_checked -> awaiting_confirmation -> mock_submitted`.

## Verification

Add deterministic `verify.py` coverage using `http.client`/in-process localhost server (not a browser):

- HTML contains `MOCK ONLY` and no real-SAP claim.
- State and each scenario endpoint are mock-only.
- Safe check/confirm/update flow returns all required states and `fixture_mutated: false`.
- Duplicate/locked/released scenarios fail with their expected safe error codes.
- Reset restores the fixture view; source fixture bytes remain unchanged.
- `/api/submit` is 404; no outbound/browser/credential imports or calls are present.
- Run `python3 verify.py` and `python3 -m py_compile app.py verify.py integration_contract.py mock_adapter.py mock_demo.py mock_sap_sandbox.py`.

Update `.agent-context/task.md`, handoff/findings/decisions, and `docs/HANDOFF.md`. Explicitly state that this sandbox tests our local contract/state handling only and does not answer Feature 6B Q1–Q11 or validate SAP selectors, permissions, side effects, or production behavior. Do not claim browser or visual verification.
