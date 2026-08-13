# Feature 9 — Friendly demo frontend

## Status

In progress. Demo-only local UI for non-technical viewers. Feature 6B remains blocked.

## Goal

Make the existing localhost `MOCK ONLY` sandbox easy to demonstrate to non-technical company viewers. This is a separate demo surface, not a real SAP frontend and not production software.

## Scope

Modify only `mock_sap_sandbox.py`, `verify.py`, `docs/RUNBOOK.md`, and coordination docs. Keep Python 3.12 standard library only; no frontend build system, package, dependency, browser automation, SAP/Edge/network/credential code, or real submission.

Use the existing sandbox API/state. Improve its embedded HTML UI into a friendly, accessible one-page guided demo:

- unmistakable top banner: `DEMO ONLY — MOCK SAP — NOT CONNECTED TO SAP`;
- plain-language explanation: “This shows how a leave request could be reviewed. Nothing is sent anywhere.”;
- large scenario buttons/cards: `Safe example`, `Already entered`, `Date unavailable`, `Period closed` mapping to safe/duplicate/locked/released;
- primary guided actions: `1. Show request`, `2. Check request`, `3. Confirm this example`, `4. Simulate update`;
- disable/enable actions according to lifecycle state; never expose a misleading real `Update` label;
- a visible progress stepper for `Request shown`, `Checked`, `Confirmation`, `Demo result`;
- plain-language result panels for success and fail-closed outcomes;
- reset button and optional technical details disclosure for JSON/state;
- keyboard/accessibility basics: labels, buttons, focus-visible styles, aria-live result, responsive layout;
- all text must say mock/demo/simulation where relevant.

Keep endpoints unchanged. Safe API flow remains `previewed -> mock_checked -> awaiting_confirmation -> mock_submitted`; failed scenarios remain duplicate/locked/released; `/api/submit` remains 404.

## Verification

- Add/adjust deterministic tests for required UI markers, accessible controls, scenario labels, no false real-SAP claims, and existing safe/failure API behavior.
- Run `python3 verify.py`, py_compile, `python3 mock_demo.py`, and fixture checksum.
- Update `docs/RUNBOOK.md` with the friendly demo steps and explicitly say the UI has not been browser/visually verified by Pi.
- No browser or visual verification may be claimed.
