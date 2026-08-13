# SARAP mag SAP local runbook

This runbook covers the local dry-run preview and the separate `MOCK ONLY` sandbox. It requires no SAP access, credentials, or external service for mock mode.

## Prerequisites

- Python 3.12.
- Optional: local Ollama for the real local preview app. The default model is `gemma4:12b`.
- No SAP account, Edge session, credentials, cookies, tokens, or selectors are needed or accepted by these local procedures.

Run commands from the project directory:

```bash
cd /mnt/c/Users/sase/project/SAP_POC
```

## Verify the project

Run the deterministic dry-run harness:

```bash
python3 verify.py
```

A successful run reports all tests passing and ends with a dry-run message stating that fake Ollama was used and SAP, Edge, network, and live Ollama access were not used.

## Run the mock lifecycle demo

The demo is in-memory and does not start the app, Ollama, a browser, SAP, Edge, or an HTTP route:

```bash
python3 mock_demo.py
```

Expected output is labeled `MOCK ONLY` and includes these states:

```text
previewed -> mock_checked -> awaiting_confirmation -> mock_submitted
```

`mock_submitted` means only that the local adapter simulated one update. It is not SAP submission evidence. The demo verifies that the fixture bytes and immutable adapter fixture remain unchanged.

## Run the `MOCK ONLY` sandbox

Start the localhost-only sandbox:

```bash
python3 mock_sap_sandbox.py --port 8993
```

The process listens on `127.0.0.1:8993` and prints a `MOCK ONLY` banner. Stop it with `Ctrl+C`.

The optional UI is at:

```text
http://127.0.0.1:8993/
```

Pi has not performed browser or visual verification; the UI address is provided only for an optional user-run local check.

### Sandbox endpoints

All sandbox responses are explicitly mock-only and all state is in memory.

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/` | `MOCK ONLY` local UI |
| `GET` | `/api/mock/state` | Discovery, redacted existing entries, and monthly status |
| `GET` | `/api/mock/plan?scenario=safe` | Load the safe deterministic plan |
| `GET` | `/api/mock/plan?scenario=duplicate` | Load the duplicate deterministic plan |
| `GET` | `/api/mock/plan?scenario=locked` | Load the locked deterministic plan |
| `GET` | `/api/mock/plan?scenario=released` | Load the released deterministic plan |
| `POST` | `/api/mock/check` | Check a previewed plan |
| `POST` | `/api/mock/confirm` | Confirm the exact unchanged plan after a successful Check |
| `POST` | `/api/mock/update` | Simulate one in-memory row update |
| `POST` | `/api/mock/reset` | Reset the in-memory adapter and lifecycle |

Unknown routes remain `404`. In particular:

```text
POST /api/submit -> 404
```

### Safe lifecycle

Use the safe scenario and call the endpoints in this order:

```text
previewed -> mock_checked -> awaiting_confirmation -> mock_submitted
```

Confirmation is fail-closed. It requires `mock_checked`, the matching checked plan, and the unchanged active preview. An unchecked or failed plan cannot be confirmed or updated. Reset returns the sandbox to `not_started`.

### Expected failure scenarios

- `duplicate` (`2026-07-16`): Check fails with `duplicate`.
- `locked` (`2026-08-17`): Check fails with `locked`.
- `released` (`2026-09-01`): Check fails with `released`.
- Confirmation before Check: fails with `check_required`.
- Confirmation after a failed Check: fails with `check_required`.
- Updates without `awaiting_confirmation`: fail closed and cannot mutate the source fixture.

## Run the local preview app

The app is one local HTTP/planning process. It serves the static page and the preview API:

```bash
python3 app.py
```

By default it listens on `127.0.0.1:8080`. The app uses local Ollama at `127.0.0.1:11434` with model `gemma4:12b` unless overridden by the existing environment variables.

The preview route is:

```text
POST /api/preview
```

It accepts only a JSON body shaped like `{"text": "..."}` and returns a validated dry-run preview or clarification. The model request uses structured JSON extraction with `think: false`; model output is validated before planning. No submission route is enabled:

```text
POST /api/submit -> 404
```

After changing source files, stop the old process with `Ctrl+C` and restart `python3 app.py`; the running Python process does not reload source changes automatically.

## Limits and safety boundary

- The sandbox is explicitly `MOCK ONLY`; `mock_submitted` is not real SAP submission evidence.
- The app and sandbox do not connect to SAP or Edge, use credentials, access cookies or tokens, make live integration calls, or submit real work or leave entries.
- Feature 6B is **BLOCKED**. It cannot be unblocked by this runbook or by the local sandbox. An approved non-production SAP environment, written Q1–Q11 owner answers, Pi authorization, and separately gated watched discovery/read/Check/Update work are required before any live integration implementation.
- No browser or visual verification has been performed or claimed. The localhost URL and optional UI instructions do not change that boundary.
