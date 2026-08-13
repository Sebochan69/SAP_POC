# Feature 8 — User-facing local runbook

## Owner

OMP writes documentation only. Pi reviews. Feature 6B remains blocked.

## Goal

Give the user one concise, copy/paste runbook for the local app and the explicit `MOCK ONLY` sandbox. Explain what each process/API does, the safe lifecycle, failure scenarios, and what local simulation cannot prove about SAP.

## Requirements

Add `docs/RUNBOOK.md` only; do not modify application code.

Include:

1. Prerequisites: Python 3.12, optional Ollama for the real local preview, no credentials or SAP access needed for mock mode.
2. Run `python3 verify.py`.
3. Run the mock-only CLI: `python3 mock_demo.py`.
4. Run the sandbox: `python3 mock_sap_sandbox.py --port 8993`; open `http://127.0.0.1:8993/` only if the user wants the UI. State explicitly that Pi has not performed browser/visual verification.
5. List sandbox endpoints and safe flow:
   `GET /`, `GET /api/mock/state`, `GET /api/mock/plan?scenario=safe|duplicate|locked|released`, POST check/confirm/update/reset.
6. Explain expected safe states: `previewed -> mock_checked -> awaiting_confirmation -> mock_submitted`; `mock_submitted` is not real SAP submission.
7. Explain expected failures: duplicate/locked/released and confirmation-before-Check fail closed.
8. Explain the local preview app: `python3 app.py`, Ollama model `gemma4:12b`, `POST /api/preview`, `/api/submit` is 404. Mention restart after source changes.
9. Explain no SAP/Edge/network/credentials behavior and Feature 6B unblock requirements in one short section.
10. Never include secrets, actual URLs, selectors, or claims of browser/visual verification.

Verify Markdown paths/commands, run `python3 verify.py`, update handoff/findings/decisions, and report no browser claim. Do not change `app.py`, `verify.py`, or sandbox code.
