# Shared decisions

- Project name: SARAP mag SAP.
- Target: local web chat assistant layered over a web-based SAP workflow.
- Coding agent: OMP. Pi coordinates and reviews.
- Model runtime: Ollama.
- Browser automation: Microsoft Edge, later; not in Feature 1.
- First implementation mode: dry-run only.
- Confirmed leave mappings: `0200` sickness; `0600` paid leave including maternal/paternal leave.
- Bulk planning remains later; Feature 3 only adds dry-run duplicate handling and monthly overview.
- Ambiguous code or duration must result in clarification, never a guess.

- Feature 1 stack: Python 3.12 standard library only (`http.server`, `urllib`, `json`, and `unittest`). This keeps the local web app, Ollama HTTP adapter, strict validation, redacted JSONL logging, and deterministic fake-model harness dependency-free.
- Verification command: `python3 verify.py`. It uses fake Ollama responses and never needs network, SAP, Edge, or a live Ollama server.
- UI boundary: the only action is a dry-run preview; there is no submission endpoint or browser automation.
- Feature 2 uses `config/philippine_holidays_2026.json`, a source-attributed, configurable holiday file from Philippine Gazette Proclamation No. 1006, s. 2025. It distinguishes `regular_holiday`, `special_non_working`, and `special_working`; no runtime Gazette scraping is used.
- Weekday/date-range expansion skips weekends and non-working holiday categories, keeps special-working days eligible, and reports every skipped date. The Gazette URL was not live-validated in this environment.
- Feature 3 uses an optional validated local JSON snapshot via `SARAP_EXISTING_ENTRIES`; no SAP fetch or runtime network call.
- Existing dates are never overwritten, and monthly status fields remain `unavailable_in_dry_run` because the local snapshot schema carries no SAP state.
- Feature 4 adds work-entry intent with mandatory Favorite WBS/project code, explicit hours/day, billable boolean, and task description. Missing or ambiguous fields produce clarification; no work defaults are guessed.

- Feature 4 verification remains fake-model and dependency-free: `python3 verify.py` passes 22 tests with no live Ollama, network, SAP, Edge, or browser access.
- Feature 5 is documentation-only SAP/Edge integration planning. It must not launch Edge, connect to SAP, add browser dependencies, use credentials, or change app code. Real submission stays disabled until a later approval.

- Feature 5 is planning only: do not edit `app.py` or `verify.py`, launch Edge, connect to SAP, use credentials, add dependencies, or enable submission.
- `docs/INTEGRATION_PLAN.md` must consume deterministic preview fields and must not invent SAP URLs, selectors, live statuses, or additional leave codes.
- A future adapter may expose only normalized reads and the explicit action states `not_started`, `previewed`, `checked`, `awaiting_confirmation`, `submitted`, and `failed`; uncertain outcomes never auto-retry.
- `Check` is not considered read-only until the approved SAP environment proves it has no side effect. `Update` requires fresh evidence and explicit user confirmation, one row at a time.
- Feature 6A is limited to an offline adapter-plan and explicit confirmation contract; it must not launch Edge, connect to SAP, use credentials, add browser dependencies, or submit. Any live adapter/Edge/SAP work is Feature 6B and remains separately gated.

- Feature 6A is offline-only and owns no browser/SAP side effect. The deterministic preview remains the sole source of planned rows.
- The adapter-plan hash covers canonical JSON including immutable preview state and confirmation requirement; confirmation never hashes or accepts arbitrary raw content.
- Only `previewed`, `awaiting_confirmation`, and `failed` are valid Feature 6A output states. Live `checked`/`submitted` states belong to Feature 6B.
- Logging is limited to `safe_log_fields` counts/categories; plan IDs, dates, WBS codes, task descriptions, user text, credentials, cookies, and tokens stay out of logs.
- Feature 6B requires all unanswered Feature 5 gates and a separate approval before any Edge launch, SAP connection, credentials, selectors/URLs, network calls, or submission.

- Pi review blocker fixes preserve the offline-only boundary: range checks, explicit leave durations, strict monthly/skip validation, and controlled failure results add no SAP/Edge/network behavior.
- `skip_summary.monthly` is a safe per-month reason/category count map used to validate monthly summary consistency before confirmation.
- `safe_log_fields` accepts only validated preview/awaiting plans or validated failed results with controlled error codes; raw failure text is rejected.

- Feature 6B preflight is documentation-only and blocked. `.agent-context/feature6b-gates.md` is the source of truth for Q1–Q11 owners, missing answers, and approval order.
- No Edge/SAP/network/browser implementation, credentials, cookies, tokens, URLs, selectors, `Check`, or `Update` action may be added or used until Pi records all gates and explicitly authorizes the next phase.
- The user must provide/confirm only the approved non-secret environment/session prerequisites and perform login/MFA personally later; secrets remain inside the user-controlled Edge session.

- Local Ollama extraction defaults to installed `gemma4:12b`; `OLLAMA_MODEL` remains the override.
- Use a documented 180-second default for cold CPU inference; `OLLAMA_TIMEOUT_SECONDS` remains the timeout override.
- Send `think: false` with the strict JSON prompt so Gemma4 returns a schema-valid extraction instead of spending the request on hidden reasoning/output drift.
- Map Ollama generate HTTP 404 to `ollama_model_not_found`; preserve `ollama_http_error` for other HTTP failures.
- Treat the local UI and preview API as one `app.py` process serving HTML at `/` and JSON at `/api/preview`; only Ollama is a separate localhost service, not a separate frontend/backend deployment.