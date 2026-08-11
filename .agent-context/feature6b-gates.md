# Feature 6B preflight gates

Status: **BLOCKED — documentation/preflight only.**

No live adapter implementation is authorized. The local dry-run planner and Feature 6A offline contract remain the only permitted behavior. No Edge session has been launched, no SAP connection or network call has been made, no credentials/cookies/tokens have been used, and no `Check`/`Update` action has been performed.

## Ownership

- **User:** confirms the approved non-secret test environment, provides/opens the watched Edge session, performs login/MFA personally, remains present for all watched work, and confirms the operational stop/abort procedure.
- **Pi:** coordinates requirements, records approvals, confirms the environment and rollout gate answers, and approves each phase transition.
- **SAP environment/process owners:** answer live workflow, side-effect, duplicate, state, and postcondition questions from the approved environment.
- **SAP UI owner:** supplies evidence-backed DOM/accessibility labels and selectors from the approved environment; no selectors are recorded here.
- **SAP reporting owner:** defines authoritative monthly/status fields and reconciliation behavior.
- **Security/audit owner:** approves prompt-injection controls, evidence redaction, retention, access, deletion, and uncertain-write handling.
- **OMP:** remains limited to documentation until Pi records all required answers and explicitly authorizes implementation; later discovery must be user-watched and read-only first.

## Missing inputs and gates

Every item is **unverified** and blocks the corresponding work until its owner supplies written evidence/answers.

| ID | Owner(s) | Missing input | Blocks |
| --- | --- | --- | --- |
| Q1 | Pi + SAP environment owner; user for session confirmation | Approved non-secret SAP test environment identifier, user-watched login/MFA procedure, session timeout/logout boundary, and environment allowlist. No environment URL is recorded yet. | Any Edge launch or discovery. |
| Q2 | OMP discovery owner + SAP UI owner | Evidence-backed labels, roles, and selectors for calendar, mode, WBS, leave code, billable, hours, task, `Check`, `Update`, and status controls in the approved environment. | Any browser interaction beyond the local dry-run. |
| Q3 | SAP process owner | Written classification of `Check` as read-only or mutating, including draft, workflow, lock, or audit side effects, plus the permitted phase. | Any `Check`; Phase 2. |
| Q4 | SAP process owner | Meaning of locked/released states, writable conditions, and manual escalation path. | Safe live reads or row actions involving those states. |
| Q5 | SAP process owner + Pi | Duplicate identity rules beyond date, with leave/work/draft/canceled examples and period/status semantics. | Phase 1 live duplicate reads. |
| Q6 | Pi + SAP process owner | Accepted partial-day leave, work-hours, billable, and mixed work/leave combinations; precision/rounding and reconciliation rules. | Single-row update design; Phase 3. |
| Q7 | SAP reporting owner | Authoritative monthly totals, balances, lock/release state, and existing-row fields mapped to the planned normalized read result. | Phase 1 monthly/status reads. |
| Q8 | SAP process owner + audit owner | Post-`Update` behavior and reliable one-row evidence proving submission; error categories and no-click-only success rule. | Any `Update`; Phase 3. |
| Q9 | Security/audit owner | Evidence redaction, retention duration, deletion, and access policy for structural/action evidence. | Discovery and all later evidence capture. |
| Q10 | Pi + security owner | Operational kill-switch/abort procedure for session changes, suspected mutation, and uncertain write outcomes; named manual reconciliation owner. | Discovery and all later phases. |
| Q11 | Security owner + OMP | Prompt-injection test cases, allowlisted action policy, page/user data boundary, and confirmation requirements. | Any adapter implementation or browser command path. |

## Approval sequence

1. **Discovery gate:** Q1, Q2, Q3, Q4, Q9, Q10, and Q11 must be answered and approved.
2. **Read-only gate:** Q5 and Q7 must be answered and normalized read schemas approved.
3. **Check gate:** Q3 must prove `Check` is non-mutating before Phase 2; otherwise `Check` remains blocked.
4. **Single-row update gate:** Q6, Q8, postcondition evidence, explicit confirmation UX, and approved Phase 2 results are required before Phase 3.
5. **Bulk gate:** Phase 4 requires separate Feature 6 approval, bounded scope, audit/retention, failure handling, and security review.

## Current decision

Feature 6B is **not ready for implementation**. Until Pi records the required answers and explicitly authorizes the next phase, do only local dry-run/documentation work. Do not infer URLs, selectors, SAP state, side effects, duplicate identity, success, or rollback behavior from screenshots or the plan.
