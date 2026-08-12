# Feature 6D — Runnable local mock lifecycle demo

## Owner

OMP implements this local-only demo. Pi reviews it. Feature 6B remains blocked.

## Context

Feature 6C mock adapter is approved in `mock_adapter.py` with fixture `config/mock_sap_2026.json`. Feature 6A offline contract is in `integration_contract.py`. Read `AGENTS.md` and `docs/HANDOFF.md` first.

## Goal

Make the mock lifecycle easy to run from a terminal so the POC can visibly demonstrate the future flow without requiring Ollama, SAP, Edge, credentials, or network.

## Requirements

Add the smallest standard-library-only executable, preferably `mock_demo.py`, that:

1. Builds one deterministic leave preview/Feature 6A plan in memory for a safe fixture date such as July 15, 2026.
2. Runs `MockSapAdapter.discover_read_only()` and displays clearly labeled `MOCK ONLY` results.
3. Runs `check_row()` on the one-row plan.
4. Calls exact `confirm_adapter_plan()` and then simulates `update_one_row()`.
5. Prints concise JSON or text showing states `previewed`, `mock_checked`, `awaiting_confirmation`, and `mock_submitted`, plus `fixture_mutated: false`.
6. Exits nonzero on failure and never changes `config/mock_sap_2026.json`.

Do not call Ollama or `app.py`; use an in-memory validated preview fixture so the demo is fast/deterministic. Do not add an HTTP route or confirmation UI. Do not present mock results as SAP results.

## Verification

- `python3 mock_demo.py` passes and visibly contains `MOCK ONLY`, `previewed`, `mock_checked`, `awaiting_confirmation`, `mock_submitted`, and `fixture_mutated: false`.
- Run `python3 verify.py` and `python3 -m py_compile app.py verify.py integration_contract.py mock_adapter.py mock_demo.py`.
- Verify fixture checksum/bytes unchanged.
- No browser/SAP/network imports or calls; `/api/submit` remains 404.
- Update docs/handoffs/findings/decisions. Explicitly keep Feature 6B blocked.


## Result

Feature 6D is implemented and approved by Pi review in `mock_demo.py` as a standard-library-only local executable. It builds and validates one in-memory July 15, 2026 sickness preview, runs mock discovery, Check, exact confirmation, and one-row in-memory update, and prints `MOCK ONLY`, `previewed`, `mock_checked`, `awaiting_confirmation`, `mock_submitted`, and `fixture_mutated: false`.

- The demo does not import or call the application, model runtime, browser, SAP, network, credentials, or HTTP routes.
- The fixture checksum and bytes remain unchanged after the simulated update; `/api/submit` remains 404.
- `python3 verify.py` passes 44 deterministic tests.
- `python3 -m py_compile app.py verify.py integration_contract.py mock_adapter.py mock_demo.py` passes.
- Feature 6B remains blocked. No browser or visual verification is claimed.