# Feature 2 — Philippine holiday-aware leave ranges

## Owner

OMP implements this feature. Pi reviews the result.

## Context

Feature 1 is approved and preserved at `.agent-context/task-01-leave-preview.md`. Read `.agent-context/philippine-holidays-research.md` before coding.

## Goal

Extend the dry-run leave preview so a simple date range expands into eligible booking dates using weekdays and a configurable Philippine holiday calendar. Keep the app dry-run only.

## Required behavior

- Support a simple date range such as `I was sick from April 2 to April 6, 2026`.
- Resolve the year when explicit; if the year is missing or ambiguous, ask for clarification rather than guessing.
- Include weekdays that are not configured as non-working holidays.
- Skip Saturdays and Sundays and report each skipped date with reason `weekend`.
- Skip configured `regular_holiday` and `special_non_working` dates and report each with its holiday name/category.
- Keep `special_working` dates eligible; do not treat them as holidays.
- Preserve the source URL and category in the holiday configuration; do not scrape the Gazette at runtime.
- If no eligible date remains, return a clear clarification/error instead of an empty successful preview.
- Keep the output useful for a future bulk planner: eligible dates, skipped dates/reasons, holiday metadata, leave type/code, and duration.
- Apply this slice to leave previews only. Do not add work/WBS entries, SAP, Edge, monthly overview, or submission.

## Holiday source

Use the researched 2026 data from Proclamation No. 1006, s. 2025 and preserve its Official Gazette URL. Categories are `regular_holiday`, `special_non_working`, and `special_working`. The research notes that the Gazette URL was not live-validated in this environment; keep that uncertainty documented and do not claim live synchronization.

## Tests / harness

Extend `python3 verify.py` with deterministic tests using the local holiday config:

- April 2–6, 2026 leaves only April 6 eligible; April 2/3 are regular holidays and April 4/5 are weekend/non-working.
- August 21, 2026 is skipped as a special non-working holiday.
- February 25, 2026 remains eligible as a special working day.
- A range with no eligible date is rejected or clarified.
- Existing Feature 1 mapping, clarification, redaction, and dry-run tests remain passing.

No network, live Ollama, SAP, or Edge access in automated tests.

## Acceptance criteria

- The local UI shows eligible and skipped dates with reasons.
- Holiday data is configurable and source-attributed.
- Date expansion is deterministic and separately testable.
- One documented verification command passes.
- `docs/HANDOFF.md` and `.agent-context/handoff.md` record the implementation, test result, and next feature.
- No real SAP side effect is possible.

## Implementation result

Feature 2 is implemented and ready for Pi review. The local calendar is `config/philippine_holidays_2026.json`; date expansion is in `app.py` and deterministic coverage is in `verify.py`.

- Verification command: `python3 verify.py`
- Result: 12 tests passed.
- Handoffs: `docs/HANDOFF.md` and `.agent-context/handoff.md`
- SAP, Edge, work/WBS, monthly overview, and submission remain disabled.
