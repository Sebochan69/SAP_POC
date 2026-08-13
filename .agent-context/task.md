# Feature 8 — User-facing local runbook

## Status

Complete. Feature 7 is approved; Feature 6B remains blocked.

Requirements are in `.agent-context/task-08-runbook.md`. Documentation only; no application code changes are requested.

The local-only structural hardening extracts the static frontend document, shared errors, and Ollama transport while preserving `app.py` routes and import compatibility. Full requirements are in `.agent-context/task-07-app-structure.md`. Review found no blockers.

## Goal

Build a small localhost-only mock SAP-like UI/API that exercises the approved Feature 6A/6C lifecycle and deterministic failure paths without Ollama, SAP, Edge, browser automation, network, credentials, or persistence.

## Requirements

See `.agent-context/task-06e-local-sandbox.md` for the full contract. Minimum:

- `mock_sap_sandbox.py`, standard-library-only, binds to `127.0.0.1` only.
- `GET /` labeled `MOCK ONLY`; no real SAP claims.
- State, deterministic safe/duplicate/locked/released plans, Check, exact confirmation, in-memory one-row update, and reset endpoints.
- Safe flow: `previewed -> mock_checked -> awaiting_confirmation -> mock_submitted`.
- Failure paths fail closed with `duplicate`, `locked`, and `released`.
- `/api/submit` remains 404; fixture remains byte-identical; no outbound/browser/credential behavior.
- Add deterministic `verify.py` tests and update coordination docs.

## Safety conclusion

This sandbox is useful for testing our own contracts, state transitions, API handling, and failure behavior. It does not answer Feature 6B Q1–Q11 and does not validate real SAP UI selectors, permissions, `Check` side effects, duplicate semantics, or production submission behavior.

## Result

Feature 6E is implemented in `mock_sap_sandbox.py` as a standard-library-only `127.0.0.1` server with a mock-only HTML UI and JSON lifecycle API. It uses in-memory validated plans and adapter state for safe, duplicate, locked, and released scenarios.

- Safe flow: `previewed -> mock_checked -> awaiting_confirmation -> mock_submitted`.
- Failure scenarios fail closed with `duplicate`, `locked`, and `released`.
- `SandboxState.confirm()` requires a successful `mock_checked` state, matching checked plan, and unchanged active preview; failed confirmation marks the sandbox failed and clears the checked-plan marker.
- Updates require `awaiting_confirmation`, so unchecked or failed plans cannot update.
- Reset reinitializes the in-memory adapter; source fixture bytes remain unchanged.
- `/api/submit` remains 404; no `app.py` route or integration behavior changed.
- `verify.py` passes 49 deterministic tests; all six Python modules compile.
- No browser or visual verification is claimed.
- Re-review confirmed no remaining Feature 6E blockers; confirmation now requires a successful Check and failed/unchecked plans cannot update.

## Feature 8 result

`docs/RUNBOOK.md` is complete as the single user-facing, documentation-only runbook. It includes copy/paste commands for `python3 verify.py`, `python3 mock_demo.py`, `python3 mock_sap_sandbox.py --port 8993`, and `python3 app.py`; the sandbox endpoint list; safe and fail-closed lifecycle states; `/api/submit` returning `404`; the restart note; and the `MOCK ONLY`/no SAP, Edge, network, credentials, browser, or visual-verification limits.

- Verification: `python3 verify.py` passes 49 deterministic tests and reports the fake-Ollama dry-run boundary.
- Feature 6B remains **BLOCKED**; the runbook does not authorize or implement live integration.
