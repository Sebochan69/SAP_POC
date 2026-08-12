# Feature 6C — Local mock SAP adapter for POC

## Owner

OMP implements this local mock. Pi reviews it. This replaces blocked live Feature 6B work for the POC; it does not answer or bypass the real SAP gates.

## Context

Features 1–6A are approved. Feature 6B remains blocked and preserved in `.agent-context/task-06b-live-gates.md`, `.agent-context/feature6b-gates.md`, and `docs/INTEGRATION_PLAN.md`. No SAP environment access is available/assumed.

## Goal

Build a deterministic local mock of the future browser adapter so the POC can exercise read, duplicate, lock/release, Check, confirmation, Update, and failure flows without Edge, SAP, credentials, network, or browser dependencies.

## Hard safety boundary

- Mock only. Never import browser libraries, launch Edge, call SAP, use network, read credentials, invent SAP URLs/selectors, or enable production submission.
- Keep `app.py` and `POST /api/preview` unchanged unless a pure local test seam is absolutely necessary; prefer a separate `mock_adapter.py` module.
- The mock must be visibly named/mock-marked in output and docs. It must never be presented as SAP behavior.
- Do not change the live Feature 6B gate artifact to claim any real gate is answered.

## Mock fixture schema

Add a local JSON fixture under `config/`, e.g. `config/mock_sap_2026.json`, with exact validated top-level keys:

```json
{
  "kind": "mock_sap_fixture",
  "name": "Local mock SAP 2026",
  "year": 2026,
  "entries": [
    {
      "date": "2026-07-16",
      "entry_kind": "work",
      "leave_code": null,
      "favorite_code": "MOCK-WBS-1",
      "hours_per_day": 8,
      "billable": true,
      "task_description": "Existing mock row",
      "state": "booked"
    }
  ],
  "monthly_status": [
    {
      "month": "2026-07",
      "locked_status": "unlocked",
      "release_status": "unreleased"
    }
  ]
}
```

Validate exact keys, dates/months, year consistency, allowed entry kinds/states, optional field types, unique row identity, and unique dates only where the fixture declares them unique. Do not reuse production names/URLs.

## Required mock seam

Add `mock_adapter.py` with deterministic, pure-local functions/classes that:

- load and validate the fixture;
- expose a clearly marked `MockSapAdapter` with `discover_read_only()`, `read_existing_entries()`, and `read_monthly_status()`;
- consume a validated Feature 6A adapter plan only—not raw text;
- compare planned rows by a documented mock identity rule (at minimum date; expose this as mock behavior, not SAP truth);
- return normalized redacted read results and mock evidence references;
- support `check_row()` as a simulated validation-only result with an explicit `mock_only` marker;
- require the Feature 6A exact plan confirmation result (`awaiting_confirmation`) before simulated update;
- support one-row simulated update only, return state/evidence, and never mutate the fixture file; use an in-memory copy;
- stop/fail closed for duplicate, locked, released, ambiguous, stale/mismatched plan, invalid row, or uncertain mock outcome;
- expose abort/kill-switch behavior that prevents further simulated updates.

Use explicit mock action states and result fields; never claim `submitted` means real SAP. Prefer `mock_submitted` or a `mock_only: true` marker alongside any state.

## Tests / verification

Extend `python3 verify.py` or add focused standard-library tests for:

- fixture validation and malformed/duplicate/invalid state rejection;
- read-only discovery and normalized existing/monthly results marked mock-only;
- duplicate skip by mock date identity;
- unlocked/unreleased row can be checked, then simulated update only after exact confirmation;
- missing/stale confirmation, locked/released/duplicate row, and abort kill switch fail closed;
- fixture file remains unchanged after simulated update;
- no browser/SAP/network imports or calls; `/api/submit` remains 404;
- all existing tests remain passing.

Run:

```bash
python3 verify.py
python3 -m py_compile app.py verify.py integration_contract.py mock_adapter.py
```

No Ollama, network, SAP, Edge, browser, credentials, or visual verification required.

## Acceptance criteria

- The POC can demonstrate the future adapter lifecycle entirely locally with unmistakable mock output.
- No real SAP gate is claimed as answered; Feature 6B remains blocked.
- No production submission route or side effect is added.
- Handoffs/findings/decisions document mock-only scope and the next action.
