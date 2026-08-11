# Feature 3 — Dry-run duplicate handling and monthly overview

## Owner

OMP implements this feature. Pi reviews the result.

## Context

Feature 1 and Feature 2 are approved and preserved in `.agent-context/task-01-leave-preview.md` and `.agent-context/task-02-holiday-ranges.md`. Read `AGENTS.md` and both files before coding.

## Goal

Extend the local, dry-run leave planner so it can compare eligible dates against a validated local existing-entry snapshot, skip duplicates without overwriting, and show a compact monthly overview. Do not add SAP, Edge, work/WBS, or submission integration.

## Existing-entry snapshot

Keep the seam deterministic and local. Add an optional `SARAP_EXISTING_ENTRIES` path for a JSON fixture; default to no existing entries so the current app behavior is unchanged. The fixture must be validated and must not be fetched from SAP.

Use the smallest useful schema:

```json
{
  "name": "Local existing entries 2026",
  "year": 2026,
  "source": {"kind": "local_fixture", "note": "Not connected to SAP"},
  "entries": [
    {"date": "2026-07-15", "label": "existing entry"}
  ]
}
```

Validate exact top-level keys, year/date formats, unique dates, and non-empty labels. Preserve source metadata in the response. Do not log entry labels or raw snapshot contents.

## Required behavior

- Compare the holiday-filtered eligible dates from Feature 2 with existing snapshot dates.
- Never overwrite or merge an existing date automatically.
- Move duplicates out of `eligible_dates` into `skipped_dates` with reason `existing_entry` and date/source metadata.
- Tell the user which dates were skipped because they already have an entry.
- Keep weekends and holidays reported exactly as Feature 2 does.
- If all candidate dates are duplicates or non-working, return `kind: "clarification"` with a useful message rather than an apparently successful empty preview.
- Keep leave code mapping and duration clarification unchanged.

## Monthly overview

Return a `monthly_overview` list grouped by `YYYY-MM` for ranges spanning one or more months. Each month should include:

- eligible/planned dates;
- full-day count;
- explicit partial-day hours (never assume hours for `full_day`);
- counts of skipped weekends, non-working holidays, and existing entries;
- `locked_status` and `release_status` as `"unavailable_in_dry_run"` unless supplied by a local snapshot. Never guess SAP state.

The overview is informational only and must carry the existing dry-run warning. It must not expose a submit/confirm action.

## API/config boundary

- Keep `POST /api/preview` as the only action route; accept the same `{"text": ...}` request shape.
- Load the optional local snapshot at startup with `SARAP_EXISTING_ENTRIES`; invalid configured files should fail fast with a clear error.
- Pass the validated snapshot into the deterministic planner. Tests may call planner/build functions with an in-memory snapshot.
- Do not add SAP, Edge, browser automation, credentials, or network calls.

## Tests / harness

Extend `python3 verify.py` while keeping all prior tests passing:

- An existing date is removed from eligible dates and appears as `existing_entry` in skipped dates.
- All candidates existing produces clarification and no planned dates.
- A range spanning two months produces two monthly overview buckets with correct planned dates and skip counts.
- A partial-day request totals explicit hours per eligible date; a full-day request does not invent an hours total.
- Malformed snapshot, duplicate snapshot date, and invalid date are rejected.
- `POST /api/submit` remains 404 and no SAP/Edge code is introduced.

No live Ollama, network, SAP, or Edge access in automated tests.

## Acceptance criteria

- `python3 verify.py` passes with one documented command.
- UI/API preview visibly includes duplicate skip information and monthly overview.
- Snapshot data is local, validated, source-attributed, and never overwritten.
- Dry-run status fields are explicit unknown/unavailable rather than guessed.
- Handoffs and findings are updated with test result and next feature.


## Implementation result

Feature 3 is implemented and approved by Pi review. The optional local existing-entry seam is loaded at startup through `SARAP_EXISTING_ENTRIES`; duplicate handling and monthly overview are deterministic in `app.py`.

Review follow-up before broader exposure: reject out-of-range snapshot/calendar years and add startup environment-loading coverage.

- Verification command: `python3 verify.py`
- Result: 17 tests passed.
- Handoffs/findings: `docs/HANDOFF.md`, `.agent-context/handoff.md`, and `.agent-context/findings.md`
- `POST /api/preview` still accepts only `{"text": ...}`; SAP, Edge, work/WBS, and submission remain disabled.