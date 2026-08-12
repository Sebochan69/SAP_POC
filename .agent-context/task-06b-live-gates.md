# Feature 6B — Live SAP/Edge adapter (gated)

## Owner

OMP owns implementation when the gates are answered. Pi coordinates and reviews. The user must provide/confirm environment access and remain present for any watched session.

## Current status

Delegated to OMP, but **blocked before live implementation**. Feature 6A is approved; its offline contract is preserved in `.agent-context/task-06a-offline-contract.md`. The Feature 5 plan is `docs/INTEGRATION_PLAN.md`.

Current missing gates:

- approved non-secret SAP test URL/environment and environment allowlist;
- available user-watched Microsoft Edge session/browser bridge;
- manual login/MFA performed by the user (never supplied to OMP, Ollama, files, or logs);
- evidence-backed DOM/accessibility discovery for the approved environment;
- written classification of `Check` as read-only or mutating;
- duplicate identity, lock/release semantics, post-Update evidence, abort, and audit/retention answers from the Feature 5 questions.

## Delegated first step

Until the gates are supplied, do **preflight/documentation only**:

1. Read `docs/INTEGRATION_PLAN.md`, `AGENTS.md`, and the preserved Feature 1–6A task files.
2. Record the gate checklist and current blocked status in `.agent-context/feature6b-gates.md` or an equivalent handoff artifact.
3. Do not edit `app.py`, `verify.py`, or `integration_contract.py` for live behavior.
4. Do not launch Edge, connect to SAP, make network calls, add browser dependencies, use credentials/cookies/tokens, invent URLs/selectors, or click `Check`/`Update`.
5. Report exactly what input is still required before implementation can begin.

## Implementation gate

No live adapter code may be written or run until Pi records all required answers and explicitly authorizes the next step. When authorized, implementation must follow `docs/INTEGRATION_PLAN.md` phases, beginning with read-only discovery, user-watched operation, deterministic preview input, no overwrite, no unattended retry, kill switch, and explicit row-level confirmation before any mutating action.

## Safety requirements for later work

- Credentials and MFA remain entirely in the user-controlled Edge session.
- The future adapter consumes validated `integration_contract.py` plans; it never interprets raw user/page text as commands.
- Unknown, locked, released, duplicate, stale-page, timeout, DOM-drift, or uncertain-write states fail closed.
- `Update`/submission is not allowed in this task without a separately approved write gate.
- No browser or visual verification may be claimed unless it actually succeeds.

## How to finish 6B

6B has two honest outcomes:

- **Finish live:** obtain an approved non-production SAP environment from an SAP environment owner, answer and approve Q1–Q11, then execute the gated phases in order: read-only discovery, read-only monthly/duplicate reads, user-watched Check only if proven non-mutating, and finally one explicitly confirmed row update with reliable postcondition evidence. Bulk remains separate.
- **Finish the POC:** stop at Feature 6E and mark 6B not implemented because no suitable SAP environment exists. The local sandbox is not SAP evidence.

The user does not need to supply credentials to this project. If a live path opens, the user personally opens the approved Edge session and performs login/MFA while remaining present. Owners provide rules/evidence; Pi records approvals; OMP implements only after authorization.

## Acceptance for this gated step

- A clear gate artifact exists with owners, missing answers, an unblock plan, and hard stops.
- No live code, connection, credential, dependency, or submission is added.
- Existing `python3 verify.py` and Feature 6A contract behavior remain unchanged.
- Handoff says implementation is blocked pending the listed user/Pi inputs.
