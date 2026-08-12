# Feature 7 — Harden local app structure

## Status

In progress. This is local-only structural cleanup; Feature 6B remains blocked.

## Goal

Reduce fragility without changing behavior by separating the static frontend document and Ollama transport from the HTTP/planning module.

## Scope

Create only the smallest useful seams:

- `static/index.html`: move the existing `HTML` document here unchanged.
- `errors.py`: own the shared feature error classes so modules do not import each other cyclically.
- `ollama_client.py`: own Ollama constants, prompt, HTTP extraction, and Ollama-specific transport behavior.
- `app.py`: remain the single process that composes HTTP routes and deterministic planning; re-export existing names (`OllamaIntentExtractor`, error classes, constants) needed by current callers/tests.

Do not split the planner yet, add a framework, create speculative backend/frontend packages, or add dependencies. Preserve:

- `GET /`, `GET /healthz`, `POST /api/preview`, and `/api/submit` 404 behavior;
- fake-model deterministic tests and public import compatibility;
- standard-library-only runtime;
- Ollama defaults/overrides, `think: false`, timeout, and error codes;
- no SAP/Edge/browser/network/credential/live-submission behavior.

## Verification

- `python3 verify.py` remains green.
- `python3 -m py_compile app.py errors.py ollama_client.py verify.py integration_contract.py mock_adapter.py mock_demo.py mock_sap_sandbox.py` passes.
- Existing HTTP preview and `/api/submit` tests pass.
- Static file is loaded by `app.py` independent of current working directory.
- `ollama_client.py` has no import of `app`, browser, SAP, Edge, or credential behavior.
- Update handoff/findings/decisions and explicitly keep Feature 6B blocked.
- No browser or visual verification claim.
