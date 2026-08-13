# Feature 6A handoff

Status: Pi review blockers fixed; approved by Pi review. Features 1–5 are approved.

Feature 6A review found no remaining blockers. Feature 6B live integration remains separately gated.

Implementation:

- `integration_contract.py` remains a standard-library-only offline seam from validated `app.py` previews to future adapter plans.
- Planned, eligible, eligible-detail, work-entry, and plan-row dates are range-checked; leave rows require explicit `full_day` or positive `hours` duration.
- Monthly summaries are validated for exact keys/types, complete month coverage, non-negative counts, fixed dry-run statuses, planned counts/hours, planned-row consistency, and skip-count consistency.
- Skip summaries retain validated per-month reason/category counts; `holiday` reasons require a matching same-date non-working holiday object, never `null` or `special_working`.
- `confirm_adapter_plan` validates the full plan, including monthly and skip summaries, before hashing; exact unchanged IDs return `awaiting_confirmation`, stale/changed IDs return a validated `failed` result.
- `safe_log_fields` validates and consumes both plan states and controlled `failed` results; failed errors are constrained to safe codes.
- Extended `verify.py` with regression coverage for all five Pi blockers. The HTTP boundary remains unchanged.
- No Edge launch, SAP connection, credentials, browser dependency, network call, selector/URL, or submission behavior was added.

Verification:

```bash
python3 verify.py
python3 -m py_compile app.py verify.py integration_contract.py
```

Result: PASS — 33 tests passed; compilation passed. No browser or visual verification is claimed.

Feature 6B live adapter work still requires answering the Feature 5 gates and separate approval.

## Feature 6B preflight

Status: **blocked before implementation**. Created `.agent-context/feature6b-gates.md` with owners, Q1–Q11 missing inputs, approval sequence, and prohibited actions.

Required user/Pi inputs:

- User/Pi + SAP environment owner: approved non-secret environment identifier/allowlist, watched Edge session, user-performed login/MFA procedure, and session boundary.
- OMP discovery owner + SAP UI owner: evidence-backed labels, roles, and selectors from that environment; none are invented in the artifact.
- SAP process owner: `Check` side-effect classification and lock/release semantics.
- SAP process owner + Pi: duplicate identity rules and examples.
- Pi + SAP process owner: partial-day/work/leave combinations, rounding, and reconciliation rules.
- SAP reporting owner: authoritative monthly/status fields and mapping.
- SAP process + audit owners: reliable post-`Update` evidence and postcondition rules.
- Security/audit owner: evidence redaction, retention, access, and deletion policy.
- Pi + security owner: kill-switch/abort and uncertain-write manual reconciliation procedure.
- Security owner + OMP: prompt-injection cases, allowlisted action policy, and confirmation requirements.

No live code, browser dependency, connection, credential, selector, URL, `Check`, or `Update` action was added or used. Pi must record all answers and explicitly authorize the next gate.

## Ollama preview bugfix

- Default model is now installed `gemma4:12b`; `OLLAMA_MODEL` remains an override.
- Default local inference timeout is 180 seconds with `OLLAMA_TIMEOUT_SECONDS` override. Gemma4 requests set `think: false` for the strict JSON extraction contract.
- Ollama generate HTTP 404 maps to `ollama_model_not_found`; other HTTP failures remain `ollama_http_error`.
- Frontend/backend are one `app.py` Python process: it serves HTML at `/` and `POST /api/preview`, then calls the separate local Ollama service. They are not separate deployments.
- Verification passed: `python3 verify.py` ran 34 tests; `python3 -m py_compile app.py verify.py integration_contract.py` passed; default-model local `POST /api/preview` returned HTTP 200 with leave code `0200` and `2026-07-15` in 47.78 seconds.
- No browser/SAP/live integration behavior was added or verified.

## Explicit-year no-guessing guard

- The preview boundary extracts explicit four-digit year tokens from the original user input.
- If no year exists, or model date years do not exactly match the explicit year set, the date range is forced to `{"start": null, "end": null}` before calendar expansion; no eligible or planned dates are produced.
- Explicit-year leave/work requests retain existing calendar handling.
- Focused regressions cover the no-year Gemma hallucination and mismatched-year cases. Verification passes 36 tests and compilation; exact `i will take a leave on Aug 20` local HTTP smoke returned 200 clarification with no planned dates in 52.05 seconds.
- The prior `ollama_http_error` may have been from an old `app.py` process. User must `Ctrl+C` and restart `python3 app.py` after updates; source changes are not hot-reloaded.
- No browser/SAP/live integration behavior was added or verified.

## Feature 6C mock POC

Real SAP access is not assumed. Feature 6C is delegated as a separate local mock adapter, defined in `.agent-context/task.md`. It may simulate the future lifecycle entirely in memory with explicit `mock_only` markers, but it does not answer Feature 6B gates or authorize live integration.

- `mock_adapter.py` and `config/mock_sap_2026.json` implement the approved local Feature 6C mock-only POC.
- The fixture is strictly validated and never written; simulated one-row updates use an in-memory copy and return `mock_submitted`, `mock_only: true`, and mock evidence references.
- `MockSapAdapter` exposes read-only discovery, normalized existing/monthly reads, date-only mock duplicate identity, Check, exact Feature 6A confirmation, fail-closed locked/released/stale/ambiguous paths, and abort/kill switch.
- `app.py`, `POST /api/preview`, and `POST /api/submit` remain unchanged; no production submission route exists.
- `verify.py` passes 43 deterministic tests; `python3 -m py_compile app.py verify.py integration_contract.py mock_adapter.py` passes.
- Feature 6B remains blocked; the mock does not answer any real SAP gate. No browser or visual verification is claimed.
- Strict fixture numeric validation rejects non-finite `hours_per_day` values via `math.isfinite`, with deterministic Python and JSON `NaN` regressions.
- Strict mock read-range validation rejects malformed, short, non-ISO, reversed, and invalid-calendar ranges with `invalid_date_range`.

## Feature 6D implemented and approved

`mock_demo.py` is a runnable standard-library-only local lifecycle demonstration. Pi review found no blockers. It builds an in-memory validated July 15, 2026 sickness preview, creates the Feature 6A plan, runs mock discovery and Check, confirms the exact plan ID, and performs one in-memory mock update.

- Output is clearly labeled `MOCK ONLY` and includes `previewed`, `mock_checked`, `awaiting_confirmation`, `mock_submitted`, and `fixture_mutated: false`.
- The demo verifies fixture bytes/checksum and the adapter's source fixture remain unchanged; no HTTP route or UI was added.
- `verify.py` passes 44 deterministic tests; `python3 -m py_compile app.py verify.py integration_contract.py mock_adapter.py mock_demo.py` passes.
- Feature 6B remains blocked; the user confirmed no non-production SAP environment is available, so Q1 cannot open discovery. No browser, visual, SAP, Edge, network, or credential behavior was added or verified.

## Feature 6B completion path

6B can finish only through an approved non-production SAP environment plus written Q1–Q11 owner answers and Pi authorization, followed by watched read-only discovery, read-only reconciliation, safe Check, and one-row explicitly confirmed Update with postcondition evidence. If no environment can be provided, the honest endpoint is Feature 6E: local/mock POC complete, 6B not implemented.

## Feature 10 completed — typed request with visual calendar block

The embedded `mock_sap_sandbox.py` page now accepts one explicit-year natural-language leave request and visually marks the matching 2026 date as `DEMO BLOCKED`. Supported forms are `August 20, 2026`, `20 August 2026`, and `2026-08-20`.

- Missing-year, invalid, unsupported-year, and ambiguous inputs show helpful client-side messages and block nothing.
- The calendar is visual-only. Typed text is never sent to an endpoint, Ollama, SAP, Edge, or network; no new endpoint or lifecycle/API/fixture behavior was added.
- `Reset calendar` and the existing `Reset demo` clear the typed request and visual block.
- Verification: `python3 verify.py` passed 51 deterministic tests; Python compilation, `python3 mock_demo.py`, direct safety/no-new-endpoint scan, and embedded JavaScript syntax check passed; fixture SHA-256 remained `f0d7df53373d79ac8c2dbfd454cd577fc8f9d699bf2259f84d74accd8098b557`.
- No browser or visual verification is claimed. Feature 6B remains **BLOCKED**.

## Feature 9 completed — friendly demo frontend

The embedded `mock_sap_sandbox.py` HTML is now a responsive, accessible, non-technical walkthrough labeled `DEMO ONLY — MOCK SAP — NOT CONNECTED TO SAP`. It uses the unchanged sandbox endpoints and lifecycle state.

- Scenario cards: `Safe example`, `Already entered`, `Date unavailable`, and `Period closed`.
- Guided actions: `1. Show request`, `2. Check request`, `3. Confirm this example`, and `4. Simulate update`; controls enable only for valid local mock states.
- Progress stepper, plain-language success/fail-closed result panels, reset, and optional technical JSON/state details are included.
- `/api/submit` remains `404`; safe and failure API behavior, in-memory state, and fixture immutability remain unchanged.
- Verification: `python3 verify.py` passed 50 deterministic tests; compilation and `python3 mock_demo.py` passed; fixture SHA-256 remained `f0d7df53373d79ac8c2dbfd454cd577fc8f9d699bf2259f84d74accd8098b557`.

## Feature 8 completed — user-facing local runbook

`docs/RUNBOOK.md` is the documentation-only copy/paste guide for the local preview and `MOCK ONLY` sandbox. It covers `python3 verify.py`, `python3 mock_demo.py`, `python3 mock_sap_sandbox.py --port 8993`, `python3 app.py`, all sandbox endpoints, safe and fail-closed failure states, `/api/submit` `404`, and restarting `app.py` after source changes.

- Verification: `python3 verify.py` passed 49 deterministic tests and the fake-Ollama dry-run harness.
- No application code, SAP, Edge, network, credentials, browser, or visual-verification behavior was added or claimed.
- Feature 6B remains **BLOCKED**.

## Feature 7 implemented — app structure hardening

The local-only change extracts the static frontend document into `static/index.html`, shared feature errors into `errors.py`, and Ollama transport into `ollama_client.py` while keeping `app.py` as the single HTTP/planning process. Routes, import compatibility, and `/api/submit` behavior remain unchanged. Pi review found no blockers; it does not add SAP/Edge behavior or unblock Feature 6B.

## Feature 6E implemented and approved

Feature 6E is an approved localhost-only sandbox slice. Pi re-review found no remaining blockers after the confirmation fail-closed fix. Its implementation remains separate from the application and is limited to local contract/state handling; Feature 6B stays blocked.

- Safe flow returns `previewed -> mock_checked -> awaiting_confirmation -> mock_submitted`.
- `safe`, `duplicate`, `locked`, and `released` scenarios use deterministic fixture dates; failure scenarios fail closed with their expected codes.
- `SandboxState.confirm()` requires lifecycle state `mock_checked`, the matching successful checked plan, and the unchanged active preview; failed or unchecked confirmation marks the sandbox failed and clears the checked-plan marker.
- Updates require lifecycle state `awaiting_confirmation`, so failed or unchecked plans cannot update.
- Reset recreates the in-memory adapter. `config/mock_sap_2026.json` remains byte-identical; `/api/submit` remains 404.
- `verify.py` passes 49 deterministic tests; `python3 -m py_compile app.py verify.py integration_contract.py mock_adapter.py mock_demo.py mock_sap_sandbox.py` passes.
- Feature 6B remains blocked; this sandbox validates only local contract/state handling and does not validate SAP selectors, permissions, `Check` side effects, duplicate semantics, or production behavior. No browser or visual verification is claimed.
