# Feature 4 — Work-entry intent and dry-run preview

## Owner

OMP implements this feature. Pi reviews the result.

## Context

Features 1–3 are approved and preserved in `.agent-context/task-01-leave-preview.md`, `.agent-context/task-02-holiday-ranges.md`, and `.agent-context/task-03-duplicate-overview.md`. Read them and `AGENTS.md` before coding.

## Goal

Add work-entry requests to the same local dry-run preview flow. Ollama may extract work intent, but deterministic validation owns required fields, date/holiday expansion, duplicate skipping, and preview safety. Do not connect to SAP or Edge.

## Input and strict model boundary

Keep `POST /api/preview` as the only action route and keep its request shape exactly `{"text": "..."}`. Extend the model response to a strict discriminated intent schema without accepting arbitrary keys:

```json
{
  "request_kind": "leave" | "work" | "unknown",
  "date_range": {"start": "YYYY-MM-DD" | null, "end": "YYYY-MM-DD" | null},
  "leave_type": "sickness" | "paid_leave" | "unknown",
  "duration": {"kind": "full_day" | "hours" | "unspecified", "hours": number | null},
  "work": {
    "favorite_code": "string" | null,
    "hours_per_day": number | null,
    "billable": true | false | null,
    "task_description": "string" | null
  }
}
```

For a leave request, preserve current Feature 1 behavior and require all `work` fields to be null. For a work request, set `leave_type` to `unknown`; leave `duration` as `unspecified`/null-hours and populate work fields. For an ambiguous request, use `request_kind: "unknown"` and ask which kind is intended. Never guess a request kind or required work field.

## Work validation

For `request_kind: "work"`:

- require an explicit date or simple range with an explicit year;
- require a non-empty Favorite WBS/project code (`favorite_code`), preserving it as user-visible data but never logging it as raw text;
- require `hours_per_day` as a positive number no greater than 24; do not infer 8 hours;
- require `billable` as an explicit boolean, including valid `false`;
- require a non-empty task description; do not invent one;
- preserve date-range, holiday filtering, local existing-entry duplicate skipping, and monthly overview from Features 2–3;
- generate one deterministic planned work entry per eligible date containing date, favorite code, hours/day, billable, and task description;
- if required fields are missing or all dates are skipped, return clarification and no planned work entries.

For non-work/leave requests, do not regress existing leave mapping (`0200`/`0600`), duration clarification, holiday behavior, duplicate handling, or monthly overview.

## Output

The preview must include `request_kind`. Work previews must include a `work_entries` list and the existing planned/skipped/monthly overview fields. Keep `dry_run: true` and the warning that no SAP or Edge action is available. Do not add a confirmation or submit action.

Work descriptions, codes, and user text must not appear in JSONL logs. Log only stage/outcome/counts and safe booleans/categories.

## Tests / harness

Extend `python3 verify.py` while keeping all existing tests passing:

- complete work request produces deterministic entries for eligible weekdays and preserves code, hours/day, billable, and task description in the preview;
- holiday/weekend behavior and existing-entry skipping still apply to work;
- missing Favorite code, missing/invalid hours, missing billable, missing task description, missing date/year, and ambiguous request kind produce clarification rather than guesses;
- explicit `billable: false` is accepted;
- model output with extra keys or wrong work field types is rejected;
- leave regression mappings/clarifications, redaction, monthly overview, and `/api/submit` 404 remain passing.

No live Ollama, network, SAP, Edge, or browser automation in automated tests.

## Acceptance criteria

- A user can submit a work request and see a validated, holiday-aware, duplicate-safe dry-run preview.
- All mandatory work fields are explicit; no defaults are guessed.
- Existing leave behavior remains passing.
- One documented command (`python3 verify.py`) passes.
- Handoffs/findings/decisions are updated with test result and next feature.
- No SAP, Edge, credentials, work submission, or real side effect is introduced.


## Implementation result

Feature 4 is implemented and approved by Pi review. `app.py` validates the discriminated leave/work schema, plans deterministic work entries, and preserves the dry-run safety boundary. `verify.py` passes 22 tests; no live Ollama, network, SAP, Edge, browser, credentials, or submission path is used.

Review follow-up: reject out-of-range snapshot/calendar years before broader exposure.