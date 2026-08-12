# Feature 1 findings

- Implemented a Python 3.12 standard-library-only local web app in `app.py`.
- The Ollama adapter extracts only a strict date-range, leave-type, and duration intent. Deterministic code owns SAP mapping and clarification decisions.
- The only action is `POST /api/preview`; there is no SAP, Edge, or submission path.
- JSONL stage logs are redacted and written to `logs/app.jsonl`, which is ignored by Git.
- `python3 verify.py` passed all 7 deterministic fake-Ollama tests.
- The running app served the dry-run page successfully at `/` during a local smoke check.

Risks remain limited to model extraction quality, unconfirmed mappings beyond `0200` and `0600`, and the intentionally unsupported holiday/bulk-booking behavior.

## Feature 2 findings

- The local JSON calendar keeps the Official Gazette URL and the three required categories.
- Expansion is inclusive and deterministic: weekends are reported as `weekend`; regular and special non-working dates are reported as `holiday` with metadata; special-working dates remain eligible.
- A missing year, unsupported calendar year, or range with no eligible date produces clarification.
- `python3 verify.py` now passes 12 tests without live Ollama, network, SAP, or Edge access.

## Feature 3 findings

- `SARAP_EXISTING_ENTRIES` is optional; absent configuration preserves the no-entry behavior.
- Configured snapshots are validated locally for exact schema, year/date shape, unique dates, and non-empty labels. Labels never enter logs or duplicate response metadata.
- Eligible holiday-filtered dates are planned only when absent from the snapshot. Existing dates move to `skipped_dates` with `existing_entry` and source metadata.
- Monthly overview buckets span every month in the requested range, count planned full days/explicit partial hours and skip categories, and expose dry-run-unavailable status fields.
- `python3 verify.py` passes 17 tests without live Ollama, network, SAP, or Edge access.
- Pi review found no Feature 3 blockers. Follow-ups: reject out-of-range snapshot/calendar years and add startup environment-loading coverage; no browser verification was performed or claimed.


## Feature 4 findings

- The strict intent schema now separates `leave`, `work`, and `unknown` requests; exact object validation rejects extra keys and invalid work field types.
- Work previews require explicit date/year, Favorite WBS/project code, positive hours/day, billable boolean including `false`, and non-empty task description. Missing fields produce clarification without work entries.
- Work entries reuse holiday/weekend expansion, existing-entry duplicate skipping, and monthly overview. Every planned date yields one deterministic preview entry.
- Work codes, task descriptions, and raw user text are not written to JSONL logs; logs retain only safe request kind, stage, outcome, and counts.
- `python3 verify.py` passes 22 tests without live Ollama, network, SAP, Edge, or browser access.
- Feature 4 is approved by Pi review; no blockers found. Follow-up: reject out-of-range snapshot/calendar years before broader exposure. Feature 5 remains separate SAP/Edge integration planning and is not approved or implemented; no browser verification was performed or claimed.

## Feature 5 findings

- `docs/INTEGRATION_PLAN.md` is a documentation-only, safety-gated design; no application code, dependencies, Edge launch, SAP connection, credentials, or submission path was added.
- The plan uses the approved deterministic preview contract from `app.py` and defines a future adapter seam without implementing it.
- POC facts, screenshot/context requirements, and interactive SAP unknowns are explicitly separated. No SAP selectors, URLs, or live workflow semantics are invented.
- Normalized existing-entry/monthly-status reads, action states, prompt-injection defenses, redaction, stale-page detection, kill switch, no-retry handling, and locked/released/duplicate failure paths are specified.
- Phases 0–4 include entry, exit, and abort/rollback policies; Phase 4 is explicitly gated behind separate Feature 6 approval.
- The documentation-only check passed. Pi review found no blockers; Feature 5 planning is approved. No browser or visual verification was performed or claimed.

## Feature 6A findings

- Pi review identified five validation gaps: range-bound dates, unspecified leave duration, weak monthly-summary validation, invalid holiday-skip semantics, and unconsumable failed results.
- `integration_contract.py` now range-checks planned/eligible/detail/work-row/plan-row dates against the relevant date range and rejects no-clarification leave previews with unspecified duration.
- Monthly summaries are checked for exact fields/types, complete month sequence, non-negative counts, fixed statuses, planned row counts/hours, and per-month/global skip-count consistency before confirmation.
- Skip summaries include validated per-month reason/category counts; `reason: "holiday"` requires a same-date regular or special non-working holiday object.
- Failed results have an exact schema, controlled error codes, and are accepted by `safe_log_fields` without exposing plan IDs or preview content.
- `verify.py` passes 33 deterministic tests, including regression coverage for all five blockers; `py_compile` passes for `app.py`, `verify.py`, and `integration_contract.py`.
- `app.py` and its HTTP boundary remain unchanged. Pi re-review found no remaining blockers; Feature 6A is approved. Feature 6B remains gated on unanswered Feature 5 environment/selector/session/side-effect questions and separate approval. No browser or visual verification was performed or claimed.

## Feature 6B preflight findings

- `.agent-context/feature6b-gates.md` records the blocked status, owners, missing Q1–Q11 inputs, approval sequence, and prohibited actions.
- No live implementation was performed: `app.py`, `verify.py`, and `integration_contract.py` were not edited; no Edge/SAP/network/credential/browser operation was used.
- User input still required: confirm the approved non-secret environment/session boundary and later perform login/MFA personally in a watched session; never provide credentials, cookies, or tokens to OMP.
- Pi/SAP/security input still required: written answers to all Q1–Q11, evidence-backed discovery/side-effect classifications, normalized read mappings, retention/abort rules, and explicit authorization for the next gate.
- Existing Feature 6A dry-run behavior and its last verified 33-test result remain unchanged. No browser or visual verification was performed or claimed.

## Ollama preview bugfix findings

- Local `/api/tags` showed installed `gemma4:12b` and `gemma4:26b`; the previous default `llama3.2:3b` was absent.
- `app.py` now defaults to `gemma4:12b` and 180 seconds for cold local CPU inference; `OLLAMA_MODEL` and `OLLAMA_TIMEOUT_SECONDS` overrides remain available.
- Gemma4 structured extraction uses `think: false`; without it, an observed full prompt response violated the strict intent schema, while the non-thinking response passed validation.
- Ollama generate HTTP 404 is surfaced as `ollama_model_not_found`; other HTTP errors remain `ollama_http_error`.
- `verify.py` passes 34 deterministic tests, compilation passes, and the default-model local `/api/preview` smoke request returned HTTP 200 with leave code `0200` and planned date `2026-07-15` in 47.78 seconds.
- The UI and preview API are served by one Python `app.py` process; Ollama is the separate localhost model service. No browser, SAP, or live integration behavior was added or verified.

## Explicit-year no-guessing guard findings

- Installed Gemma4 can return HTTP 200 with an invented year for input containing only a month and day.
- `app.py` now validates model date years against explicit four-digit year tokens in the original user text at the preview boundary.
- Missing explicit years and mismatched model years force an unresolved date range before expansion, so clarification responses contain no eligible or planned dates.
- Existing explicit-year leave/work and calendar handling remains covered by the prior regression suite.
- `verify.py` passes 36 deterministic tests; compilation passes; the exact no-year local HTTP request returned HTTP 200 clarification with no planned dates in 52.05 seconds.

## Feature 6C mock-only findings

- Real SAP access is unavailable; the approved replacement is strictly local and mock-only.
- `config/mock_sap_2026.json` uses exact validated fixture keys, 2026-consistent dates/months, unique date/month identities, and explicit lock/release states.
- `MockSapAdapter` returns redacted normalized reads with `mock_only: true`, `mock_fixture` provenance, mock evidence references, and an explicit date-only identity rule.
- Check, exact Feature 6A confirmation, one-row in-memory update, and abort/kill-switch behavior are deterministic and fail closed for duplicate, locked, released, stale, ambiguous, invalid, multi-row, and aborted paths.
- The fixture bytes remain unchanged after simulated update. `POST /api/submit` remains 404 and `app.py`/live HTTP behavior were not edited.
- `verify.py` passes 42 tests and all four Python modules compile. Feature 6B remains blocked; no browser or visual verification is claimed.
- The prior `ollama_http_error` may have been produced by a stale long-running app process; restart with `Ctrl+C` and `python3 app.py` after updates. No browser/SAP/live integration behavior was added or verified.

## Feature 6C strict numeric fixture validation

- `hours_per_day` now rejects NaN and positive/negative infinity with `math.isfinite` while preserving the existing positive 0–24 range.
- Regression coverage rejects Python non-finite floats and a JSON `NaN` fixture value; `verify.py` passes 42 deterministic tests and all four modules compile.
- Feature 6C remains mock-only and Feature 6B remains blocked; no browser, SAP, network, credential, or API changes were made.

## Feature 6C strict mock read-range validation

- `_range_bounds` now checks the complete ISO date shape before extracting the year, so malformed, short, and non-ISO ranges fail with `MockAdapterError("invalid_date_range")` instead of leaking `ValueError`.
- The focused regression covers `xxxx-01-01`, a short `2026-01`, and `2026/01/01`; the existing reversed and invalid-calendar checks remain unchanged.
- Full verification passes 43 deterministic tests; `python3 -m py_compile app.py verify.py integration_contract.py mock_adapter.py` passes. No browser or visual verification was performed.
- Feature 6C remains mock-only; `app.py`, `/api/preview`, `/api/submit`, fixture immutability, and Feature 6B blocked status are unchanged. No browser or visual verification is claimed.