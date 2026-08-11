# SAP/Edge Integration Plan

**Feature:** 5 — planning only
**Status:** Draft for Pi review; no implementation is approved
**Scope:** Future, user-watched Microsoft Edge integration for the existing local dry-run planner

This document is an implementation-ready design boundary, not an automation implementation. Feature 5 does not launch Edge, connect to SAP, use credentials, add dependencies, edit `app.py` or `verify.py`, or add a submission route. Feature 6 requires separate approval before any implementation or real side effect.

## 1. Observed SAP workflow and unknowns

### Evidence rules

The plan uses three evidence classes:

- **POC facts:** behavior and fields already defined by the local application and approved task records. These are safe input/output contracts, not evidence of live SAP behavior.
- **Screenshot/context requirements:** visual workflow concepts supplied for planning. Screenshots can guide discovery vocabulary and expected review points, but do not authorize writes and do not establish stable selectors, URLs, or side-effect semantics.
- **Interactive unknowns:** anything that must be confirmed in the actual approved SAP environment by a user watching the session. Unknowns remain unknown in normalized results; the adapter must not guess.

No SAP URL, DOM selector, accessibility label, account detail, or secret is recorded here. No screenshot-derived selector is promoted into an implementation contract.

### Workflow inventory

| Workflow area | POC fact or requirement | What remains unverified interactively |
| --- | --- | --- |
| Calendar/date selection | The deterministic planner emits an explicit date or year-bearing simple range and filters weekends and configured Philippine holidays. | Which calendar control is used; whether dates are selected per row, as a range, or through a monthly grid; timezone and locale behavior; how an unavailable/locked date is surfaced. |
| Favorite WBS/project code | A work preview requires an explicit non-empty `favorite_code`; the value is preserved in preview data and excluded from logs. | Whether the UI uses a Favorite WBS dropdown, autocomplete, code input, or project/task hierarchy; allowed code format; whether the list is user/session-specific; how an invalid or inactive code is reported. |
| Work versus leave | `request_kind` is the local discriminated intent: `leave`, `work`, or `unknown`. Unknown intent requires clarification before planning. | Exact UI control and whether work and leave use separate screens, tabs, or row modes; whether switching mode clears fields; which combinations SAP accepts. |
| Leave code | Confirmed POC mappings are sickness → `0200` and paid leave, including maternal/paternal leave → `0600`. | The live field label and available options; whether the displayed label differs from the code; whether the live system has additional policies or codes that must remain outside this plan. |
| Billable status | A work preview requires an explicit boolean, including `false`; no default is inferred. | Exact control and default behavior; whether billable is available for every work code; whether changing it affects totals or approval state. |
| Hours/day | A work preview requires a positive explicit value no greater than 24; leave hours are explicit only when requested. | Accepted precision, rounding, decimal separator, maximum by task/policy, and whether hours are entered per row or as a period total. |
| Task description | A work preview requires a non-empty task description; no text is invented. | Field length, allowed characters, required formatting, and whether the live UI stores a separate note/category. |
| `Check` | The future workflow may use `Check` only as a validation step after a fresh local preview. | Whether `Check` is read-only, creates a draft, changes state, triggers workflow, or has any side effect. Until proven read-only, treat it as potentially mutating. |
| `Update`/submission | Any `Update` or equivalent action is outside the current app and must require explicit user confirmation after a fresh preview. | Exact action label, confirmation behavior, row/period scope, response semantics, and reliable post-submit evidence. |
| Monthly overview | The local preview groups requested months and reports planned dates, full-day/partial-hour totals, weekend/holiday/existing-entry skips, and `unavailable_in_dry_run` lock/release statuses. | Whether SAP exposes a monthly grid, totals, balances, lock state, release state, or draft state; which values are authoritative and how they map to dates/rows. |
| Existing entries | The local optional fixture identifies existing dates and causes duplicates to be skipped without overwrite or merge. | Live duplicate identity beyond date: leave/work type, code, WBS, task, hours, status, and period; whether existing drafts count as booked; how canceled/released rows appear. |

### Current contract boundary

The approved local planner remains the source of truth for candidate rows. Its preview includes `dry_run`, `kind`, `request_kind`, `date_range`, `leave_type`, `sap_code`, `duration`, `eligible_dates`, `planned_dates`, `eligible_date_details`, `skipped_dates`, holiday metadata, existing-entry metadata, `monthly_overview`, `work_entries`, warnings, and clarifications. A future adapter consumes validated preview data; it does not reinterpret raw user text or ask a model to choose SAP actions.

## 2. Proposed adapter seam

### Contract and ownership

`app.py` remains the deterministic planner and owns:

- strict intent validation;
- leave mapping (`0200`/`0600` only where currently confirmed);
- date/year resolution and holiday expansion;
- duplicate exclusion using the validated local seam;
- planned leave/work rows, warnings, and clarifications;
- dry-run status values when live SAP state is unavailable.

A future browser adapter owns only interaction with an already approved, user-watched Edge session. It must not change planner decisions, invent missing fields, or silently convert a preview into a submission.

The following is a design-level interface, not code to add in Feature 5:

```text
BrowserAdapter
  discover_read_only(session) -> DiscoveryReport
  read_existing_entries(session, requested_range) -> ExistingEntryRead
  read_monthly_status(session, requested_range) -> MonthlyStatusRead
  apply_preview_row(session, planned_row) -> ActionResult
  check_row(session, planned_row) -> ActionResult
  update_one_row(session, planned_row, confirmation_token) -> ActionResult
  abort(session) -> AbortResult
```

The adapter must receive structured `planned_row` data from the local preview. It must not receive or log credentials, raw session cookies, unrestricted page text, or arbitrary model-generated commands. `discover_read_only` is the only operation allowed before the relevant rollout gate.

### Normalized read results

All live reads must normalize into stable, redacted records. Unknown fields remain `null` or an explicit `unknown` status; raw page text is evidence only and is never treated as an instruction.

```text
ExistingEntryRead {
  status: ok | unavailable | ambiguous | failed,
  source: live_sap_read,
  entries: [
    {
      date: YYYY-MM-DD,
      entry_kind: leave | work | unknown,
      leave_code: string | null,
      favorite_code: string | null,
      hours_per_day: number | null,
      billable: true | false | null,
      task_description_present: true | false | null,
      row_identity: opaque_local_reference | null,
      state: booked | draft | locked | released | unknown
    }
  ],
  evidence_ref: redacted_local_reference | null,
  warnings: [safe_category]
}

MonthlyStatusRead {
  status: ok | unavailable | ambiguous | failed,
  months: [
    {
      month: YYYY-MM,
      planned_count: number | null,
      existing_count: number | null,
      total_hours: number | null,
      locked_status: locked | unlocked | unknown,
      release_status: released | unreleased | unknown,
      evidence_ref: redacted_local_reference | null
    }
  ],
  warnings: [safe_category]
}
```

`row_identity` is an adapter-local opaque reference only. It must not be guessed from a date when the live page exposes multiple rows for that date. `source` is provenance, not permission to overwrite local fixtures or submit data.

### Action state machine

The adapter exposes exactly these states:

- `not_started`: no live interaction for this preview.
- `previewed`: local planner produced a valid preview and the user saw it; no SAP write occurred.
- `checked`: a specific row was sent through a verified read-only `Check` flow and the result was captured. If `Check` side effects are not proven absent, this state is not allowed.
- `awaiting_confirmation`: a fresh preview, fresh page read, and row-level evidence match; the adapter is paused for explicit user confirmation of one action.
- `submitted`: only after explicit confirmation, a bounded update action, and reliable post-action evidence for that row.
- `failed`: ambiguity, timeout, DOM drift, lock/release conflict, validation failure, or uncertain side effect. No automatic retry follows `failed`.

Allowed normal progression is:

```text
not_started -> previewed -> checked -> awaiting_confirmation -> submitted
                         \-> failed
checked ------------------\-> failed
awaiting_confirmation ----\-> failed
```

A live read that disagrees with the local preview invalidates `awaiting_confirmation` and returns to `failed`; it must not be silently refreshed into a new submission. `submitted` is never inferred from a button click alone.

No SAP URL or selector is specified until Phase 0 discovery produces evidence and Pi approves the result.

## 3. Safe browser workflow

This workflow is future design only. It is not executable in Feature 5.

1. **Preflight the local preview.** Require `kind: "preview"`, no unresolved clarifications, explicit dates/fields, and at least one planned row. Recheck that every planned date is absent from the local existing-entry seam. A warning or unavailable live status is not permission to guess.
2. **User login and MFA.** The user opens the approved SAP environment and completes login/MFA. The adapter never receives credentials, passwords, MFA codes, recovery codes, or session tokens as planner input. No unattended login is allowed.
3. **Read-only discovery first.** Inspect the current page and accessibility tree, identify the active period and mode, and capture only redacted structural evidence. Do not fill fields or click `Check`, `Update`, or equivalent controls during discovery.
4. **Read live entries before filling.** Normalize existing rows and monthly status. Compare by the verified live identity rules, beginning with date. If a date is already booked, ambiguous, locked, released, or otherwise not safely writable, skip and report it; never overwrite or merge automatically.
5. **Reconcile the fresh read.** The adapter must compare the live period, row identity, requested date, work/leave mode, code, WBS, hours, billable state, and task requirements with the local preview. Any mismatch stops the run and invalidates confirmation.
6. **Fill one planned row at a time.** Use semantic labels/accessibility roles where possible after discovery. Scope each operation to the selected row/period, use allowlisted values from the deterministic preview, and verify each field after entry. Stop on ambiguous matches, duplicate controls, missing labels, validation errors, or DOM drift.
7. **Use `Check` only under the gate.** In Phase 2, a user watches the session. `Check` is permitted only after its side-effect behavior is verified and the row matches the fresh preview. Capture validation evidence without retaining sensitive values. If `Check` might create a draft or trigger workflow, stop and classify it as a write.
8. **Confirm before `Update`.** In Phase 3, show the exact one-row action summary, fresh live-read evidence, and dry-run warning. Require an explicit user confirmation tied to that row and current page state. Never treat a stale confirmation as valid after navigation, timeout, or page mutation.
9. **Verify or stop.** After an approved one-row update, read the resulting row/status and record redacted evidence. If post-action state is ambiguous, mark `failed` and do not retry. The user can abort at any point through a kill switch that stops further interaction and leaves the page for manual inspection.
10. **No unattended bulk behavior.** Phase 4, if separately approved, still runs row-by-row with per-row evidence, bounded scope, stop-on-error, and a user-visible abort path. It never retries a row whose submission outcome is uncertain.

### Prompt-injection boundary

SAP page text, task descriptions, and user text are data. They cannot issue browser commands. The future adapter must:

- pass only validated, typed preview fields into an allowlisted action dispatcher;
- keep page text out of action-selection prompts, or treat any model output as untrusted suggestions requiring deterministic validation and user confirmation;
- reject instructions embedded in descriptions, page banners, notes, or error messages that request credential disclosure, selector changes, extra navigation, or submission;
- never let a model choose arbitrary URLs, selectors, JavaScript, keyboard sequences, retries, or confirmation decisions;
- require the human confirmation gate for every action that can mutate SAP state.

## 4. Security and failure handling

### Credential and session boundaries

- Login, MFA, cookies, and session state remain inside the user-controlled Edge session.
- Credentials and tokens never enter Ollama prompts, JSONL logs, local fixtures, source files, screenshots, plan artifacts, or test fixtures.
- Local logs contain stage, outcome, safe categories, counts, and opaque evidence references only. They do not contain raw user text, task descriptions, WBS codes, page text, or secrets.
- A future adapter must use least privilege and an environment allowlist approved by Pi/SAP owners. The environment identifier must be explicit before discovery.

### Safety controls

- Apply operation and navigation timeouts; treat timeout after a possible click as an uncertain outcome, not as a retryable failure.
- Use a stale-page/DOM fingerprint or equivalent structural check before each row action. A changed period, mode, row count, or control identity invalidates the current preview.
- Keep a kill switch that stops queued actions, detaches the adapter from further input, and leaves the session for the user.
- Do not use unattended retries. A retry, if ever allowed after a confirmed read-only failure, requires a fresh read and user-visible approval; never retry after a possible `Update`.
- Record redacted evidence for discovery, Check, update, and post-action reads with timestamps and action state. Retain only what the approved audit policy permits.

### Failure matrix

| Condition | Required result | Automatic action |
| --- | --- | --- |
| Row is already booked or duplicate identity matches | Skip the row; report `existing_entry`/duplicate evidence; preserve the existing row. | No overwrite, merge, or retry. |
| Row is locked | Mark row unavailable/locked and stop if scope cannot be safely narrowed. | No fill or update. |
| Row is released or period is closed | Treat as non-writable until the owner defines a safe workflow. | No unlock/reopen attempt. |
| Existing row identity is ambiguous | Mark `ambiguous`; ask the user or Pi/SAP owner to resolve identity rules. | No selection by position or date alone. |
| `Check` returns a validation error | Capture safe error category and mark the row failed or clarification-required. | Do not press `Update`. |
| DOM/accessibility structure changes | Mark `failed`, capture redacted structural evidence, and stop. | No selector guessing or retry. |
| Timeout after a possible write | Mark outcome uncertain/failed and require manual inspection. | Never automatically retry. |
| Network/session loss before a confirmed postcondition | Mark failed/unknown; user verifies the live row manually. | No automatic re-submit. |
| Prompt injection or suspicious page instruction | Treat content as untrusted data and stop the action path. | No credential disclosure or command execution. |

## 5. Phased rollout

Every phase is gated by written approval and evidence from the previous phase. The current application remains unchanged throughout Feature 5.

### Phase 0 — Selector and flow discovery, no writes

**Entry criteria**

- Approved SAP environment and account/MFA owner identified.
- User is present in a watched session.
- Scope is limited to read-only page inspection; no credentials are supplied to the adapter.
- A redaction/evidence policy and kill switch are approved.

**Exit criteria**

- The calendar, mode controls, WBS/project field, leave code field, billable/hours/task fields, monthly overview, existing-row representation, `Check`, and `Update` controls are documented with evidence references.
- Exact labels/selectors are captured from the approved environment, not invented from screenshots.
- Side effects of `Check` and `Update` are explicitly classified.
- Unknowns and DOM drift risks are recorded for Pi review.

**Rollback/abort**

Stop the session immediately on unexpected navigation, credential prompt, ambiguous control, or sensitive data exposure. Delete unapproved evidence and leave SAP state untouched; no write rollback is needed because this phase permits no writes.

### Phase 1 — Read-only monthly overview capture

**Entry criteria**

- Phase 0 evidence is approved.
- Read-only access can identify the requested period and existing rows without filling or mutating controls.
- Normalized `ExistingEntryRead` and `MonthlyStatusRead` schemas are approved.

**Exit criteria**

- A watched session can capture dates, existing entries, totals, lock/release states, and safe evidence references.
- Duplicate identity rules and unknown status handling are validated against representative rows.
- The adapter can reconcile live reads with a local dry-run preview without proposing an overwrite.

**Rollback/abort**

Abort on any side effect, mismatch, or ambiguous identity. Discard the read result for planning purposes and require a fresh read after the issue is resolved. No SAP update is permitted.

### Phase 2 — Fill and `Check`, user-watched, no `Update`

**Entry criteria**

- Phase 1 read reconciliation is approved.
- `Check` has been verified as non-mutating in the approved environment; if not, Phase 2 is blocked.
- Semantic/accessibility selectors and stale-page detection are tested.
- User watches the entire session; scope is one or a small explicitly bounded set of rows, with no Update control available to the adapter.

**Exit criteria**

- Each filled row matches the deterministic preview and produces captured validation evidence.
- Duplicate, locked, released, already-booked, validation-error, timeout, and DOM-drift paths stop safely.
- No Update/submission action was sent.

**Rollback/abort**

Use the kill switch on any mismatch or suspected mutation. Clear only fields proven to be local/uncommitted if the UI supports that safely; otherwise stop and let the user inspect. Never attempt an automated compensating update.

### Phase 3 — Explicit-confirmation `Update`, one row only

**Entry criteria**

- Phase 2 is approved and `Update` side effects/postconditions are documented.
- One row has a fresh local preview, fresh live read, verified identity, and successful Check evidence.
- The user receives a row-level summary and explicitly confirms this exact action.
- Post-update verification and audit retention are available.

**Exit criteria**

- Exactly one confirmed row is updated.
- The post-action read identifies the resulting row/status without relying only on a click result.
- Evidence is redacted and the state transition is recorded as `submitted` only after verification.

**Rollback/abort**

Abort before Update if any page state changes. After a possible Update, do not retry or issue an automatic inverse action; mark the row failed/uncertain and require manual SAP review. Any correction is a separate user-approved action.

### Phase 4 — Bounded bulk submission, separate approval required

**Entry criteria**

- Feature 6 is separately approved with security, audit, environment, and operational sign-off.
- Phase 3 is stable, per-row evidence and postconditions are reliable, and explicit row bounds are configured.
- The user confirms the batch scope after a fresh preview and live duplicate read.

**Exit criteria**

- Rows are processed sequentially with per-row state/evidence.
- The run stops on the first ambiguous, failed, locked, released, duplicate, timeout, or uncertain outcome unless the approved policy explicitly says otherwise.
- A final report distinguishes submitted, skipped, failed, and unknown rows without claiming success from missing evidence.

**Rollback/abort**

The user can stop between rows. There is no automatic rollback or retry for uncertain rows; manual reconciliation is required. Batch submission is not implemented or approved by Feature 5.

## 6. Open questions and approval gates

All questions below are **unverified**. Each must be answered and recorded by the named owner before the corresponding implementation gate can open.

| ID | Unverified question | Owner | Required answer before implementation |
| --- | --- | --- | --- |
| Q1 | What exact SAP URL/environment is approved, and how are account, MFA, session timeout, and logout handled? | Pi + SAP environment owner | Approved environment identifier, user-watched login procedure, and session boundary. |
| Q2 | What are the exact DOM/accessibility labels, roles, and selectors for calendar, mode, WBS, code, billable, hours, task, Check, Update, and status controls? | OMP discovery owner + SAP UI owner | Evidence-backed selector map for the approved environment; no screenshot-only selectors. |
| Q3 | Does `Check` have any side effect, including draft creation, workflow, locking, or audit logging? | SAP process owner | Written classification as read-only or mutating and the permitted rollout phase. |
| Q4 | What do locked and released states mean, and which state transitions are user-authorized? | SAP process owner | Read-only interpretation, writable conditions, and manual escalation path. |
| Q5 | What identifies a duplicate beyond date: mode, leave code, WBS, task, hours, status, or period? | SAP process owner + Pi | Normalized identity rule and examples for leave/work/draft/canceled rows. |
| Q6 | How are partial-day leave, work hours/day, billable state, and mixed work/leave requests represented and totaled? | Pi + SAP process owner | Accepted combinations, precision/rounding, and reconciliation rules. |
| Q7 | What monthly totals, balances, lock state, release state, and existing-row data are authoritative? | SAP reporting owner | Field-level mapping to `MonthlyStatusRead` and conflict behavior. |
| Q8 | What happens after Update, and what evidence proves one row was submitted? | SAP process owner + audit owner | Stable postcondition, error categories, and no-click-only success rule. |
| Q9 | What evidence may be retained, for how long, and who may access it? | Security/audit owner | Redaction, retention, deletion, and access policy for structural/action evidence. |
| Q10 | What is the approved abort/kill-switch behavior if the session changes or a write outcome is uncertain? | Pi + security owner | Operational stop procedure and manual reconciliation owner. |
| Q11 | How are user/page instructions isolated from browser commands and credentials? | Security owner + OMP | Prompt-injection test cases, allowlisted action policy, and confirmation requirements. |

### Approval gates

1. **No implementation gate:** this document is reviewed for completeness while the app stays local/dry-run.
2. **Discovery gate:** Q1, Q2, Q3, Q4, Q9, Q10, and Q11 must be answered before any future Edge adapter is written or launched.
3. **Read-only gate:** normalized live reads, duplicate identity, and monthly status mapping (Q5 and Q7) must be approved before Phase 1.
4. **Check gate:** Q3 must prove `Check` is non-mutating before Phase 2; otherwise the workflow skips directly to a separately approved write-safety design.
5. **Single-row update gate:** Q6 and Q8, postcondition evidence, explicit confirmation UX, and Phase 2 results must be approved before Phase 3.
6. **Bulk gate:** Feature 6 must separately approve Phase 4, bounded scope, audit/retention, failure operations, and security review.

Until these gates are satisfied, the only permitted behavior is the existing local dry-run preview and documentation review.
