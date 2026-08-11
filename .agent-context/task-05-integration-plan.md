# Feature 5 — SAP/Edge integration plan (no implementation)

## Owner

Pi defines the safety requirements. OMP drafts the plan and reviews it for implementation feasibility. No agent may launch Edge, connect to SAP, use credentials, or change the application code in this feature.

## Context

Features 1–4 are approved and preserved in `.agent-context/task-01-leave-preview.md` through `.agent-context/task-04-work-preview.md`. Read `AGENTS.md`, `docs/HANDOFF.md`, the screenshots already reviewed, and those task records.

## Goal

Produce a concrete, implementation-ready plan for a future SAP web UI integration through Microsoft Edge, while keeping the current application completely dry-run and local. This feature is documentation/research only.

## Deliverable

Create `docs/INTEGRATION_PLAN.md` and update `docs/HANDOFF.md`, `.agent-context/handoff.md`, `.agent-context/findings.md`, and `.agent-context/decisions.md`. Do not edit `app.py`, `verify.py`, or add browser/SAP dependencies.

The plan must cover:

1. **Observed SAP workflow and unknowns**
   - calendar/date selection;
   - Favorite WBS/project code;
   - work versus leave selection;
   - leave code (`0200`/`0600`);
   - billable status, hours/day, task description;
   - `Check` versus `Update`/submission;
   - monthly overview, existing entries, totals, lock status, release status.
   Clearly separate facts from screenshots/POC requirements and items that must be verified interactively.

2. **Proposed adapter seam**
   - Keep `app.py` deterministic planner output as the input contract.
   - Define a browser adapter interface at the level of intent/preview, without implementing it.
   - Define normalized read results for existing entries and monthly status.
   - Define action states: `not_started`, `previewed`, `checked`, `awaiting_confirmation`, `submitted`, `failed`.
   - No SAP selectors or URLs may be invented; mark them as discovery work.

3. **Safe browser workflow**
   - User performs login/MFA; credentials never enter Ollama, logs, fixtures, or source files.
   - Read-only discovery first; inspect the page and existing entries before filling anything.
   - Reuse the deterministic holiday/duplicate planner; never overwrite an existing date.
   - Fill one planned row at a time, use semantic selectors where possible, and stop on ambiguity or DOM drift.
   - `Check` may be allowed only as a validation step; `Update`/submit must be behind an explicit user confirmation after a fresh preview.
   - Record evidence without sensitive values; provide a kill switch/abort path and avoid unattended retries.

4. **Security and failure handling**
   - Credential/session boundaries, local-only logging, redaction, timeouts, stale-page detection, partial-failure recovery, and no automatic retry of a potentially submitted row.
   - Explain how to prevent prompt injection from SAP page text and user text from becoming browser commands.
   - Define what happens if a row is locked, released, already booked, or the SAP page changes.

5. **Phased rollout**
   - Phase 0: selector/flow discovery with no writes.
   - Phase 1: read-only monthly overview capture.
   - Phase 2: fill-and-Check in a user-watched session, no Update.
   - Phase 3: explicit-confirmation Update for one row only.
   - Phase 4: approved bounded bulk submission with per-row evidence and stop-on-error.
   Each phase needs entry/exit criteria and a rollback/abort policy.

6. **Open questions and approval gates**
   - SAP URL/environment and account/MFA behavior;
   - exact DOM/accessibility labels and selectors;
   - whether Check has side effects;
   - meaning of lock/release states;
   - duplicate identity beyond date;
   - handling of partial-day and work/leave combinations;
   - audit/evidence retention.
   Mark each as `unverified`, assign an owner, and state what must be answered before implementation.

## Verification

- Verify the document contains all six sections, explicit no-code/no-connection boundaries, and no credentials or real URLs/secrets.
- Use a simple repeatable check such as a small Python assertion script or documented grep command; do not require SAP, Edge, network, or Ollama.
- Do not claim browser or visual verification.

## Acceptance criteria

- `docs/INTEGRATION_PLAN.md` is complete enough for a later implementation task without inventing SAP details.
- The current dry-run app and `python3 verify.py` remain unchanged and passing.
- No SAP/Edge/network/browser code, credentials, or submission route is added.
- Handoffs explicitly say Feature 5 is planning only and Feature 6 requires separate approval.

## Result

Feature 5 planning is complete and approved by Pi review. The documentation-only check and `python3 verify.py` pass; no application code or integration was added. Feature 6 remains unapproved.
