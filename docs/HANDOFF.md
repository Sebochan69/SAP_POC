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

## Next feature

Feature 6B (live adapter, Edge launch, SAP connection, credential use, or submission) is not approved.
