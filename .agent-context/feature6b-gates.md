# Feature 6B preflight gates

Status: **BLOCKED — no non-production SAP environment available.**

The user confirmed that no non-production SAP environment is available. Q1 cannot be satisfied without an SAP environment owner provisioning or approving one. No live adapter implementation is authorized. The local dry-run planner and Feature 6A offline contract remain the only permitted behavior. No Edge session has been launched, no SAP connection or network call has been made, no credentials/cookies/tokens have been used, and no `Check`/`Update` action has been performed.

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

Feature 6B is **not ready for implementation**. The user has no non-production SAP environment, so the discovery gate cannot open. Keep the project local/mock-only and do only dry-run/documentation work unless an SAP environment owner later provides an approved non-production environment and the remaining Q1–Q11 answers. Do not infer URLs, selectors, SAP state, side effects, duplicate identity, success, or rollback behavior from screenshots or the plan.

## How Feature 6B can finish

Feature 6B cannot be completed by the local sandbox alone. It can finish only through one of these explicit decisions:

1. **Live SAP path:** an SAP environment owner provides an approved non-production environment and the written Q1–Q11 answers below are obtained; or
2. **Mock-only POC path:** the project is intentionally stopped at the local dry-run/mock scope, and Feature 6B is recorded as blocked/not implemented. Feature 6E is the final local simulation, not live SAP integration.

### Live SAP path

1. **Environment owner:** provide a non-secret environment alias/client, approved environment allowlist, session timeout/logout boundary, and the user-watched login/MFA procedure. The user opens the environment and performs login/MFA personally; do not send credentials, MFA codes, cookies, or tokens here.
2. **Owner answers:** obtain written answers from the SAP environment, UI, process, reporting, and security/audit owners for Q1–Q11. Screenshots alone do not establish selectors or side effects.
3. **Pi approval:** Pi records the answers, redaction/retention policy, abort procedure, and explicit authorization for Phase 0. No Edge/SAP code is written before this point.
4. **Phase 0 discovery:** user watches a read-only session while OMP identifies evidence-backed labels/roles/selectors and records only approved redacted structural evidence. No field fill, `Check`, or `Update`.
5. **Phase 1 reads:** after Q5/Q7 approval, read existing rows/monthly status and reconcile them with a fresh local plan. Duplicate, locked, released, or ambiguous rows are skipped/fail closed.
6. **Phase 2 Check:** only if Q3 proves `Check` is non-mutating. Run user-watched, bounded, no-`Update` tests and approve the results.
7. **Phase 3 one-row Update:** only after Q6/Q8, postcondition evidence, explicit confirmation UX, and Phase 2 approval. The user confirms one exact row; verify the resulting row/status. Never infer success from a click.
8. **Bulk:** optional and separately approved. It is not part of the current completion gate.

### Copy/paste owner request

```text
We need written answers for the SARAP mag SAP Feature 6B gates in an approved non-production environment:
Q1 environment/session boundary; Q2 UI labels/roles/selectors; Q3 Check side effects;
Q4 locked/released semantics; Q5 duplicate identity; Q6 partial-day/work reconciliation;
Q7 authoritative monthly/status fields; Q8 Update postcondition evidence;
Q9 evidence redaction/retention; Q10 abort/manual reconciliation; Q11 prompt-injection/action allowlist.
Please identify the owner for each answer and provide evidence-backed rules. Do not send credentials,
MFA codes, cookies, tokens, or production data. The user will perform login/MFA in a watched session.
```

### Hard stop conditions

- No approved non-production environment: Q1 is blocked; do not launch Edge or connect to SAP.
- Unknown `Check` side effects: Phase 2 is blocked.
- Unknown post-`Update` evidence: Phase 3 is blocked.
- Missing owner approval or uncertain identity/state: stop; do not guess or retry.
- No credentials, cookies, tokens, URLs, selectors, or raw SAP/page text belong in this repository or chat.
