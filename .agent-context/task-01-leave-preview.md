# Feature 1 — Leave intent and dry-run preview

## Owner

OMP implements this feature. Pi reviews the result.

## Goal

Build the smallest local web chat flow for a user to enter a leave request, use Ollama to extract structured intent, validate it, and display a preview. This feature must not connect to SAP or Edge and must not submit anything.

## Required behavior

- Input such as `I was sick on July 15, 2026` extracts a leave request for that date and maps sickness to SAP code `0200`.
- Input describing paid leave maps to SAP code `0600`.
- Input such as `I will be on leave on July 15, 2026` is ambiguous and must ask which leave code/type to use.
- If duration/quantity is absent, do not silently assume it; show a clarification request for full-day or hours.
- Preserve the date/range shape in the model schema, but only implement one date or a simple date range if it stays minimal. Do not implement bulk booking yet.
- Show a clear preview containing date(s), leave type, SAP code, duration state, and warnings/clarifications.
- No SAP browser automation, holiday logic, existing-entry checks, monthly overview, or real submission in this slice.

## AI boundary

Use a small Ollama adapter. The model extracts intent only. Deterministic code owns code mapping, required-field validation, and preview state. Tests must use a fake model adapter and must not require a running Ollama server.

## Required project plumbing

- Structured JSONL logs for parse/validate/preview stages; do not log raw user text or secrets by default. Ignore runtime logs in Git.
- One repeatable verification command (for example `npm run verify`) that runs deterministic tests and a dry-run harness.
- The harness must cover: sickness → `0200`, paid leave → `0600`, ambiguous leave → clarification, and invalid model output → validation error.
- Create/update `docs/HANDOFF.md` with status, decisions, commands, test results, risks, and the next feature.

## Acceptance criteria

- The app runs locally with one documented command.
- A user can submit text and see a validated preview or a specific clarification question.
- Ollama is configurable locally; no credentials are hardcoded.
- Strict schema validation rejects malformed model output.
- The automated verification command passes without SAP, Edge, network, or live Ollama access.
- No real SAP side effect is possible from this feature.

## Implementation result

Feature 1 is implemented and ready for Pi review. The dependency-free app is in `app.py`; deterministic fake-Ollama verification is in `verify.py`.

- Verification command: `python3 verify.py`
- Result: 7 tests passed.
- Handoff: `docs/HANDOFF.md` and `.agent-context/handoff.md`
- Findings: `.agent-context/findings.md`
