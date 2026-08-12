# Feature 6E — Local SAP-like sandbox

## Status

In progress. The user has no non-production SAP environment, so this is a controlled local simulation only. Feature 6B remains blocked.

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
