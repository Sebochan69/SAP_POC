# Feature 10 — Typed leave request with visual calendar block

## Status

In progress. Feature 9 is approved; Feature 6B remains blocked.

## Goal

Make the demo more useful for non-technical viewers: let someone type a natural-language leave request and see the explicit date visually blocked on a local calendar.

Example:

```text
I will take vacation leave on August 20, 2026.
```

The page should show August 2026 and mark August 20 as `DEMO BLOCKED`.

## Scope and safety

- Modify only `mock_sap_sandbox.py`, `verify.py`, `docs/RUNBOOK.md`, and coordination docs.
- Keep Python 3.12 standard-library-only; no build system, package, browser automation, SAP/Edge/network/credential code, or new endpoint.
- This is client-side visual demo state only. Do not send the typed text to any endpoint, Ollama, SAP, Edge, or network. Do not modify the existing sandbox lifecycle/API or fixture.
- Label the feature clearly as `DEMO ONLY` / `MOCK ONLY`; say that the calendar block is visual simulation and does not create or submit a real entry.
- Never guess a year. Require an explicit four-digit year. Support the simple English date forms `August 20, 2026`, `20 August 2026`, and ISO `2026-08-20`; invalid/ambiguous input must show a helpful message and block nothing.
- The local demo calendar is limited to fixture year 2026. A valid date outside 2026 must explain that this demo calendar covers 2026 and block nothing.

## UI requirements

Add a prominent panel to the existing friendly sandbox page:

- Heading such as `Type a request and see the demo calendar`.
- Accessible label and textarea/input with an example placeholder.
- Button such as `Block date on demo calendar`.
- `aria-live` status explaining detected date, missing year, invalid date, unsupported year, or success.
- Calendar grid with month/year heading, weekday labels, valid day cells, and a clear legend.
- The typed date gets a visually prominent class/label `DEMO BLOCKED`.
- Existing fixture dates may be shown as `Example entry`, but do not imply SAP data.
- Responsive/focus-visible styles consistent with the current page.
- Reset clears the typed request and visual calendar block without changing the sandbox API reset semantics.
- Keep the existing scenario-card lifecycle demo working.

## Verification

- Add deterministic `verify.py` source/HTML marker coverage for the input, button, calendar grid, `DEMO BLOCKED`, visual-only wording, explicit-year/parser markers, and no-new-endpoint boundary.
- Run `python3 verify.py` (expected 51 tests or more), py_compile, `python3 mock_demo.py`, and fixture SHA-256 check.
- Run a direct source scan proving no new outbound/browser/SAP behavior and no typed text endpoint call.
- Update `docs/RUNBOOK.md` with the typed-date walkthrough and explicit no-browser/visual-verification statement.
- No browser or visual verification may be claimed by Pi.
