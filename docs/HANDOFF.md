# SARAP mag SAP handoff

## Status

Features 1–4 are approved by Pi review. The app remains local and dry-run only: it has no SAP, Edge, credential, network, or submission integration.

Feature 3 review found no blockers. Follow-up before broader exposure: reject out-of-range snapshot/calendar years and add startup environment-loading coverage.


## Feature 3 implemented

The leave preview now compares holiday-filtered eligible dates with an optional validated local existing-entry snapshot and returns a compact monthly overview.

- Configure a local snapshot with `SARAP_EXISTING_ENTRIES`; absent configuration means no existing entries and preserves prior behavior.
- Snapshot files use exact top-level keys `name`, `year`, `source`, and `entries`.
- Snapshot dates must be valid, unique, within the snapshot year, and have non-empty labels.
- Snapshot source metadata is preserved in the response; labels and raw snapshot contents are never logged.
- Existing dates move out of `eligible_dates` into `skipped_dates` with reason `existing_entry` and source metadata. No date is overwritten or merged.
- If every candidate is an existing entry or non-working, the preview returns `kind: "clarification"` with a useful message.
- `monthly_overview` spans every month in the requested range and reports planned dates, full-day count, explicit partial-day hours, weekend/holiday/existing-entry skip counts, dry-run warnings, and `unavailable_in_dry_run` lock/release statuses.
- Monthly overview is informational only and exposes no submit or confirm action.

## Feature 4 implemented

The preview now accepts a strict discriminated leave/work intent and produces deterministic work entries without adding a submission action.

- Work requests require an explicit year-bearing date/range, Favorite WBS/project code, positive hours/day, billable boolean, and non-empty task description.
- Missing or ambiguous request/work fields return clarification and no planned work entries; no defaults are guessed.
- Work entries reuse holiday expansion, weekend/holiday skip reporting, local existing-entry duplicate skipping, and monthly overview.
- Work output contains `request_kind: "work"` and `work_entries`; codes, descriptions, and user text are never written to JSONL logs.
- Leave mappings, clarifications, redaction, duplicate handling, monthly overview, and `/api/submit` 404 remain preserved.


## Safety and API boundary

- `POST /api/preview` remains the only action route and still accepts only `{"text": ...}`.
- SAP, Edge, credentials, network calls, real work/WBS submission, and real side effects remain absent.
- Feature 1 mappings/duration clarification and Feature 2/3 holiday, duplicate, and monthly-overview behavior remain preserved.

## Decisions

- Python 3.12 standard library only; no package install is required.
- Existing entries are a local fixture seam only; invalid configured files fail fast at startup.
- SAP lock/release state is never guessed. The local fixture schema contains no SAP state, so statuses remain `unavailable_in_dry_run`.
- Work-entry fields remain preview-only; no SAP state is inferred.

## Verification

Command run:

```bash
python3 verify.py
```

Result: **PASS — 22 tests passed.** Coverage includes Feature 1–3 regressions, deterministic work entries, holiday/weekend filtering, duplicate skipping, missing-field clarifications, explicit `billable: false`, strict work-schema rejection, redacted logs, monthly overview, and the absence of a submission route.

The local app starts with:

```bash
python3 app.py
```

## Risks and limits

- Existing-entry snapshots are manually maintained local fixtures and may be stale.
- Monthly lock/release status is intentionally unavailable until a separately approved integration supplies it.
- Model extraction can still misclassify natural-language leave/work intent; strict validation rejects unsafe output rather than guessing.
- SAP, Edge, work submission, duplicate-resolution workflows, and broader integration remain out of scope.

## Feature 5 planning

Feature 5 is documentation-only and approved by Pi review. `docs/INTEGRATION_PLAN.md` defines a safety-gated future SAP/Edge adapter without implementing or approving any browser, SAP, credential, network, or submission behavior.

Review found no blockers. Feature 6 remains required before any adapter implementation, Edge launch, SAP connection, credential use, or submission.

- The plan separates local POC facts, screenshot/context requirements, and interactive SAP unknowns.
- The local `app.py` preview remains the future adapter input contract; no selectors or SAP URLs are invented.
- The plan defines normalized live-read results, action states, prompt-injection boundaries, failure handling, a kill switch, and phased rollout gates from read-only discovery through separately approved bounded bulk work.
- Every listed SAP question is marked `unverified` with an owner and a required answer before implementation.
- Repeatable documentation-only check:
```bash
python3 -c 'from pathlib import Path; t=Path("docs/INTEGRATION_PLAN.md").read_text(encoding="utf-8"); assert all(f"## {n}." in t for n in range(1, 7)); assert not any(x in t for x in ("http://", "https://", "-----BEGIN")); assert "Feature 6 requires separate approval" in t; print("integration plan documentation check: PASS")'
```
- Result: **PASS**. No browser or visual verification is claimed. The current dry-run app and `python3 verify.py` remain unchanged.

## Feature 6A implemented; Pi blockers fixed

Feature 6A remains an offline-only adapter contract and explicit confirmation gate. `integration_contract.py` consumes only complete validated previews; it never launches Edge, connects to SAP, handles credentials, makes network calls, or submits anything.

- Canonical plans use stable SHA-256 `plan_id` values, `state: "previewed"`, `requires_confirmation: true`, normalized leave/work rows, and safe monthly/skip summaries.
- Planned dates, eligible dates, eligible-date details, work-row dates, and plan-row dates must remain inside the preview/plan date range. Leave previews must carry an explicit `full_day` or `hours` duration.
- Monthly summaries validate exact field types, non-negative ranges, unavailable-in-dry-run statuses, planned counts/hours, month coverage, planned-row consistency, and skip-count consistency before confirmation.
- `reason: "holiday"` skips require a same-date `regular_holiday` or `special_non_working` holiday object; `null` and `special_working` are rejected.
- Exact plan-ID confirmation returns `awaiting_confirmation`; stale or changed plans fail closed. Failed results have a strict schema and are safe for `safe_log_fields`; `checked` and `submitted` are not produced.
- `safe_log_fields` exposes counts/categories or a controlled failure code only; plan IDs, dates, WBS codes, task descriptions, user text, credentials, cookies, and tokens are not logged.
- `POST /api/preview` and the current `app.py` planner remain unchanged. Feature 6B live adapter work still requires all unanswered Feature 5 gates and separate approval.

Verification:

```bash
python3 verify.py
python3 -m py_compile app.py verify.py integration_contract.py
```

Result: **PASS — 33 tests passed; compilation passed.** No browser or visual verification is claimed.

## Feature 6C mock POC

Feature 6C is approved as a local mock-only adapter because real SAP access is unavailable. It is a deterministic in-memory POC and does not answer or bypass Feature 6B.

- `mock_adapter.py` loads and strictly validates `config/mock_sap_2026.json`.
- The fixture is immutable; simulated updates append only to an in-memory copy.
- `MockSapAdapter` exposes clearly marked mock-only discovery, existing-entry, monthly-status, Check, exact Feature 6A confirmation, one-row simulated update, and abort/kill-switch paths.
- Date-only duplicate identity is documented as mock behavior, not SAP truth.
- Duplicate, locked, released, ambiguous, stale, invalid, multi-row, and aborted paths fail closed.
- Results use `mock_only: true`, mock evidence references, and `mock_submitted`; no real `submitted` state or production route was added.
- `POST /api/submit` remains 404. `app.py` and live HTTP behavior remain unchanged.
- Strict numeric fixture validation rejects non-finite `hours_per_day` values via `math.isfinite`; deterministic regressions cover Python NaN/infinities and JSON `NaN`.
- Strict read-range validation rejects malformed, short, non-ISO, reversed, and invalid-calendar ranges as `invalid_date_range`; deterministic regression covers malformed, short, and non-ISO inputs.

Feature 6B remains **BLOCKED**. The user confirmed that no non-production SAP environment is available, so Q1 cannot open discovery. Its remaining Q1–Q11 environment, selector, side-effect, identity, audit, security, and approval gates remain unchanged.

Verification:

```bash
python3 verify.py
python3 -m py_compile app.py verify.py integration_contract.py mock_adapter.py
```

Result: **PASS — 43 deterministic tests passed; compilation passed.** No browser or visual verification is claimed.
## Feature 6D implemented and approved

`mock_demo.py` is a runnable local lifecycle demonstration using a standard-library-only executable and an in-memory validated preview. Pi review found no blockers. It exercises the approved mock adapter without invoking the application, model runtime, browser, SAP, Edge, credentials, network, or HTTP routes.

- The demo uses July 15, 2026 sickness (`0200`) because the mock fixture has an unlocked/unreleased July status and no row on that date.
- Output is clearly labeled `MOCK ONLY` and includes `previewed`, `mock_checked`, `awaiting_confirmation`, `mock_submitted`, and `fixture_mutated: false`.
- Fixture bytes/checksum and the adapter's immutable source fixture remain unchanged; `POST /api/submit` remains 404.
- Forbidden-import coverage rejects browser/network/application/model-runtime imports in the mock adapter and demo.

Feature 6B remains **BLOCKED**. The user confirmed that no non-production SAP environment is available, so Q1 cannot open discovery. Its remaining Q1–Q11 environment, selector, side-effect, identity, audit, security, and approval gates remain unchanged.

Verification:

```bash
python3 mock_demo.py
python3 verify.py
python3 -m py_compile app.py verify.py integration_contract.py mock_adapter.py mock_demo.py
```

Result: **PASS — demo lifecycle states verified; 44 deterministic tests passed; compilation passed.** No browser or visual verification is claimed.
## Feature 6B preflight

Status: **BLOCKED — preflight/documentation only.** The complete gate checklist is `.agent-context/feature6b-gates.md`.

Remaining inputs are Q1–Q11 from the Feature 5 plan: approved non-secret environment/session boundary (Pi + SAP environment owner, confirmed by the user), evidence-backed UI labels/selectors (OMP discovery + SAP UI owner), `Check` side-effect classification (SAP process owner), lock/release semantics (SAP process owner), duplicate identity (SAP process owner + Pi), work/leave and partial-day reconciliation (Pi + SAP process owner), authoritative monthly/status mapping (SAP reporting owner), post-`Update` evidence (SAP process + audit owners), evidence retention (security/audit owner), abort/kill-switch procedure (Pi + security owner), and prompt-injection/action allowlisting (security owner + OMP).

The user must confirm the watched-session/environment prerequisites and perform login/MFA personally when a later gate opens; no credentials, cookies, tokens, URLs, or selectors are requested or recorded here. Pi must record every answer and explicitly authorize implementation before any Edge/SAP work. Until then, only the local dry-run preview and documentation review are permitted.

## Local Ollama preview fix

The local model path now defaults to the installed `gemma4:12b`; `OLLAMA_MODEL` remains an explicit override. The default request timeout is 180 seconds to allow cold CPU model loading and inference, while `OLLAMA_TIMEOUT_SECONDS` remains an override. Structured Gemma4 extraction sends `think: false` so the JSON-only contract is usable. Ollama generate HTTP 404 responses now return `ollama_model_not_found`; other HTTP failures remain `ollama_http_error`.

The frontend and backend are not separate deployments. One `app.py` Python process serves the HTML page at `GET /` and the JSON preview API at `POST /api/preview`; that process calls the separate local Ollama service at `127.0.0.1:11434`.

Verification:

```bash
python3 verify.py
python3 -m py_compile app.py verify.py integration_contract.py
```

Result: **PASS — 34 deterministic tests passed; compilation passed.** An actual local default-model smoke request to `POST /api/preview` with `gemma4:12b` returned HTTP 200, `request_kind: "leave"`, SAP code `0200`, and planned date `2026-07-15` in 47.78 seconds. No browser or visual verification is claimed. No SAP or live integration behavior was added.

## Explicit-year no-guessing guard

The preview boundary now extracts explicit four-digit year tokens from the original user text. If no year is present, or the validated model date years do not exactly match the explicit year set, the date range is replaced with unresolved `null` values before calendar expansion. The result is a clarification with no eligible or planned dates. Explicit-year leave/work requests retain the existing calendar and year handling.

Focused regressions cover a model-invented year for `i will take a leave on Aug 20` and a model year that conflicts with an explicit `2026`. Verification now passes **36 deterministic tests**. The exact local HTTP smoke returned HTTP 200 with `kind: "clarification"`, a null date range, and no planned dates in 52.05 seconds.

The previous `ollama_http_error` may have come from an old long-running `app.py` process. After updates, stop it with `Ctrl+C` and restart `python3 app.py`; the process does not reload source changes automatically. No browser or visual verification is claimed.
