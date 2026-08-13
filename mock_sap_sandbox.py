"""Feature 6E controlled localhost-only mock sandbox."""

from __future__ import annotations

import copy
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any

import integration_contract as contract
import mock_adapter
import mock_demo

HOST = "127.0.0.1"
DEFAULT_PORT = 8993
MOCK_LABEL = "MOCK ONLY"
SCENARIOS = {
    "safe": "2026-07-15",
    "duplicate": "2026-07-16",
    "locked": "2026-08-17",
    "released": "2026-09-01",
}

HTML = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Demo only — Mock SAP</title>
<style>
:root {
  color-scheme: light;
  --ink: #1c2434;
  --muted: #536174;
  --paper: #ffffff;
  --canvas: #f3f6fb;
  --line: #d6deea;
  --blue: #155eef;
  --blue-dark: #0d47b5;
  --green: #137333;
  --green-bg: #e8f5ec;
  --red: #a12622;
  --red-bg: #fff0ef;
  --amber: #875400;
  --amber-bg: #fff7df;
  --focus: #ff9f1c;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  background: var(--canvas);
  color: var(--ink);
  font: 16px/1.5 system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}
button, summary { font: inherit; }
button {
  min-height: 46px;
  border: 1px solid var(--blue);
  border-radius: 10px;
  padding: .7rem 1rem;
  background: var(--blue);
  color: #fff;
  cursor: pointer;
  font-weight: 700;
}
button:hover:not(:disabled) { background: var(--blue-dark); }
button:disabled { cursor: not-allowed; opacity: .45; }
button:focus-visible, summary:focus-visible {
  outline: 3px solid var(--focus);
  outline-offset: 3px;
}
.page-shell { max-width: 1160px; margin: 0 auto; padding: 1rem; }
.hero {
  border-radius: 18px;
  padding: 1.5rem 1.75rem;
  background: #16213e;
  color: #fff;
  box-shadow: 0 10px 28px #17213e22;
}
.banner-line {
  margin: 0;
  color: #ffd166;
  font-size: clamp(1.35rem, 3vw, 2.25rem);
  font-weight: 900;
  letter-spacing: .04em;
}
.hero p { margin: .35rem 0 0; }
.hero-note { color: #e4ecff; max-width: 65ch; }
main { display: grid; gap: 1rem; margin-top: 1rem; }
.panel, .scenario-card, .result-panel, details {
  border: 1px solid var(--line);
  border-radius: 14px;
  background: var(--paper);
  box-shadow: 0 5px 18px #17213e0d;
}
.intro, .panel, .result-panel, details { padding: 1.25rem; }
h1, h2, h3 { line-height: 1.2; }
h1 { margin: 0 0 .4rem; font-size: clamp(1.5rem, 4vw, 2.4rem); }
h2 { margin: 0 0 .7rem; font-size: 1.25rem; }
h3 { margin: 0 0 .35rem; font-size: 1rem; }
p { max-width: 70ch; }
.eyebrow {
  margin: 0 0 .35rem;
  color: var(--blue-dark);
  font-size: .78rem;
  font-weight: 800;
  letter-spacing: .1em;
  text-transform: uppercase;
}
.scenario-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: .75rem;
}
.scenario-card {
  min-height: 132px;
  padding: 1rem;
  color: var(--ink);
  text-align: left;
  transition: transform .15s ease, border-color .15s ease, box-shadow .15s ease;
}
.scenario-card:hover:not(:disabled), .scenario-card.is-selected {
  border-color: var(--blue);
  box-shadow: 0 0 0 3px #155eef22;
  transform: translateY(-2px);
}
.scenario-card.is-selected { background: #eef4ff; }
.scenario-card span { display: block; }
.card-title { margin-bottom: .35rem; font-weight: 800; }
.card-copy { color: var(--muted); font-size: .92rem; }
.demo-layout {
  display: grid;
  grid-template-columns: minmax(240px, .8fr) minmax(0, 1.2fr);
  gap: 1rem;
}
.stepper {
  display: grid;
  gap: .65rem;
  list-style: none;
  margin: 0 0 1rem;
  padding: 0;
}
.stepper li {
  display: flex;
  align-items: center;
  gap: .65rem;
  color: var(--muted);
  font-weight: 700;
}
.stepper li span:first-child {
  display: grid;
  width: 30px;
  height: 30px;
  place-items: center;
  border: 2px solid var(--line);
  border-radius: 50%;
  background: var(--paper);
}
.stepper li.is-done, .stepper li.is-current { color: var(--blue-dark); }
.stepper li.is-done span:first-child {
  border-color: var(--green);
  background: var(--green);
  color: #fff;
}
.stepper li.is-current span:first-child {
  border-color: var(--blue);
  color: var(--blue);
}
.actions { display: grid; gap: .6rem; }
.secondary {
  border-color: var(--line);
  background: #fff;
  color: var(--blue-dark);
}
.secondary:hover:not(:disabled) { background: #eef4ff; }
.reset {
  width: 100%;
  margin-top: .8rem;
  border-color: #7b8798;
  background: #fff;
  color: var(--ink);
}
.request-box {
  margin-top: .8rem;
  border-left: 4px solid var(--blue);
  padding: .8rem 1rem;
  background: #f3f7ff;
}
.request-box p { margin: .25rem 0; }
dl { display: grid; grid-template-columns: max-content 1fr; gap: .35rem .8rem; margin: 1rem 0 0; }
dt { color: var(--muted); font-weight: 700; }
dd { margin: 0; }
.result-panel[data-kind="success"] { border-color: #9fd3aa; background: var(--green-bg); }
.result-panel[data-kind="failure"] { border-color: #e2aaa6; background: var(--red-bg); }
.result-panel[data-kind="info"] { border-color: #f0ce77; background: var(--amber-bg); }
.result-panel p { margin-bottom: 0; }
.state-label { color: var(--muted); font-size: .9rem; font-weight: 700; }
details { padding: .9rem 1.25rem; }
summary { cursor: pointer; font-weight: 800; }
pre {
  overflow: auto;
  margin: .8rem 0 0;
  padding: .8rem;
  border-radius: 8px;
  background: #17213e;
  color: #e9efff;
  font-size: .82rem;
}
footer {
  padding: 1.25rem 0 .5rem;
  color: var(--muted);
  font-size: .9rem;
  text-align: center;
}
@media (max-width: 820px) {
  .scenario-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .demo-layout { grid-template-columns: 1fr; }
}
@media (max-width: 500px) {
  .page-shell { padding: .65rem; }
  .hero, .intro, .panel, .result-panel, details { padding: 1rem; }
  .scenario-grid { grid-template-columns: 1fr; }
}
</style>
</head>
<body data-demo="mock-sap-sandbox" data-mode="demo-only">
<div class="page-shell">
<header class="hero" data-ui-marker="demo-banner">
  <p class="banner-line">DEMO ONLY — MOCK SAP — NOT CONNECTED TO SAP</p>
  <p class="hero-note">A friendly walkthrough of a leave-request review. This is a local simulation for demonstration only.</p>
</header>
<main>
  <section class="intro panel" aria-labelledby="intro-title">
    <p class="eyebrow">A guided local simulation</p>
    <h1 id="intro-title">See a leave request move through a review</h1>
    <p>This shows how a leave request could be reviewed. Nothing is sent anywhere.</p>
    <p>Choose an example below, then follow the four demo steps. Every result is kept in memory and marked as a simulation.</p>
  </section>

  <section aria-labelledby="scenario-title">
    <p class="eyebrow">Pick a story to tell</p>
    <h2 id="scenario-title">Choose a demo example</h2>
    <div class="scenario-grid" data-ui-marker="scenario-cards" role="group" aria-label="Demo examples">
      <button type="button" class="scenario-card is-selected" data-scenario="safe" aria-pressed="true">
        <span class="card-title">Safe example</span>
        <span class="card-copy">A new request can continue through the mock review.</span>
      </button>
      <button type="button" class="scenario-card" data-scenario="duplicate" aria-pressed="false">
        <span class="card-title">Already entered</span>
        <span class="card-copy">The mock check finds the date already in the example data.</span>
      </button>
      <button type="button" class="scenario-card" data-scenario="locked" aria-pressed="false">
        <span class="card-title">Date unavailable</span>
        <span class="card-copy">The mock check stops because the date is unavailable.</span>
      </button>
      <button type="button" class="scenario-card" data-scenario="released" aria-pressed="false">
        <span class="card-title">Period closed</span>
        <span class="card-copy">The mock check stops because the period is closed.</span>
      </button>
    </div>
  </section>

  <section class="demo-layout" aria-label="Guided demo">
    <div class="panel">
      <p class="eyebrow">Follow along</p>
      <h2>Demo progress</h2>
      <ol class="stepper" id="progress-stepper" data-ui-marker="progress-stepper" aria-label="Demo progress">
        <li id="step-request"><span aria-hidden="true">1</span><span>Request shown</span></li>
        <li id="step-checked"><span aria-hidden="true">2</span><span>Checked</span></li>
        <li id="step-confirmation"><span aria-hidden="true">3</span><span>Confirmation</span></li>
        <li id="step-result"><span aria-hidden="true">4</span><span>Demo result</span></li>
      </ol>
      <div class="actions" aria-label="Guided demo actions">
        <button type="button" id="show-request" data-demo-action="show-request">1. Show request</button>
        <button type="button" id="check-request" data-demo-action="check-request" disabled>2. Check request</button>
        <button type="button" id="confirm-example" data-demo-action="confirm-example" disabled>3. Confirm this example</button>
        <button type="button" id="simulate-update" data-demo-action="simulate-update" disabled>4. Simulate update</button>
      </div>
      <button type="button" class="reset" id="reset-demo" data-demo-action="reset">Reset demo</button>
    </div>

    <section class="panel" aria-labelledby="request-title">
      <p class="eyebrow">What the example says</p>
      <h2 id="request-title">Demo request</h2>
      <p id="request-copy" aria-live="polite">Choose an example, then select “1. Show request”.</p>
      <div class="request-box" id="request-detail" hidden>
        <p><strong>Example request:</strong> <span id="request-text"></span></p>
        <dl>
          <dt>Date</dt><dd id="request-date"></dd>
          <dt>Type</dt><dd id="request-type">Sickness leave (demo)</dd>
          <dt>Duration</dt><dd id="request-duration">Full day (demo)</dd>
        </dl>
      </div>
    </section>
  </section>

  <section class="result-panel" id="result-panel" data-ui-marker="result-panel" data-kind="neutral" aria-live="polite" aria-atomic="true">
    <p class="eyebrow">Plain-language result</p>
    <h2 id="result-title">Ready for a demo</h2>
    <p id="result-copy">Nothing has been checked. This page is a local simulation.</p>
    <p class="state-label" id="state-label">Demo state: not_started</p>
  </section>

  <details id="technical-details" data-ui-marker="technical-details">
    <summary>Technical details (JSON/state)</summary>
    <pre id="technical-output">{}</pre>
  </details>
</main>
<footer>MOCK ONLY. This demonstration is not connected to SAP and does not submit anything.</footer>
</div>
<script>
const SCENARIO_COPY = {
  safe: {
    date: "July 15, 2026",
    request: "I was sick on July 15, 2026.",
    shown: "A new demo request is ready to review."
  },
  duplicate: {
    date: "July 16, 2026",
    request: "I was sick on July 16, 2026.",
    shown: "This demo request uses a date already in the example data."
  },
  locked: {
    date: "August 17, 2026",
    request: "I was sick on August 17, 2026.",
    shown: "This demo request uses a date marked unavailable."
  },
  released: {
    date: "September 1, 2026",
    request: "I was sick on September 1, 2026.",
    shown: "This demo request uses a date in a closed demo period."
  }
};
const FAILURE_COPY = {
  duplicate: "Already entered — the demo stopped safely.",
  locked: "Date unavailable — the demo stopped safely.",
  released: "Period closed — the demo stopped safely.",
  check_required: "Check required — the demo stopped safely.",
  invalid_state: "This demo step is not available yet.",
  stale_plan: "This demo request is no longer current."
};
const $ = (id) => document.getElementById(id);
const scenarioCards = [...document.querySelectorAll("[data-scenario]")];
const steps = [...document.querySelectorAll("#progress-stepper li")];
let selectedScenario = "safe";
let plan = null;
let confirmation = null;
let lifecycle = "not_started";
let completedSteps = 0;
let lastResponse = null;

function showResult(kind, title, message) {
  $("result-panel").dataset.kind = kind;
  $("result-title").textContent = title;
  $("result-copy").textContent = message;
}

function failureTitle(code) {
  return FAILURE_COPY[code] || "The demo stopped safely.";
}

function technicalState() {
  $("technical-output").textContent = JSON.stringify({
    mock_only: true,
    scenario: selectedScenario,
    state: lifecycle,
    plan,
    confirmation,
    last_response: lastResponse
  }, null, 2);
}

function render() {
  $("check-request").disabled = !(lifecycle === "previewed" && plan);
  $("confirm-example").disabled = !(lifecycle === "mock_checked" && plan);
  $("simulate-update").disabled = !(lifecycle === "awaiting_confirmation" && confirmation);
  $("state-label").textContent = `Demo state: ${lifecycle}`;
  steps.forEach((step, index) => {
    step.classList.toggle("is-done", index < completedSteps);
    step.classList.toggle("is-current", lifecycle === "failed" ? index === 3 : index === completedSteps);
  });
  technicalState();
}

function chooseScenario(event) {
  selectedScenario = event.currentTarget.dataset.scenario;
  plan = null;
  confirmation = null;
  lifecycle = "not_started";
  completedSteps = 0;
  lastResponse = null;
  scenarioCards.forEach((card) => {
    const selected = card === event.currentTarget;
    card.classList.toggle("is-selected", selected);
    card.setAttribute("aria-pressed", String(selected));
  });
  $("request-detail").hidden = true;
  $("request-copy").textContent = "Example selected. Select “1. Show request” to begin.";
  showResult("neutral", "Ready for a demo", "Nothing has been checked. This page is a local simulation.");
  render();
}

async function apiCall(path, options) {
  const response = await fetch(path, options);
  const body = await response.json();
  return {ok: response.ok, body};
}

function handleFailure(body) {
  lifecycle = body.state || "failed";
  confirmation = null;
  showResult("failure", failureTitle(body.error), "Nothing was sent anywhere. Choose another example or reset the demo.");
  render();
}

async function showRequest() {
  try {
    const result = await apiCall(`/api/mock/plan?scenario=${selectedScenario}`);
    lastResponse = result.body;
    if (!result.ok || !result.body.plan) {
      handleFailure(result.body);
      return;
    }
    plan = result.body.plan;
    confirmation = null;
    lifecycle = result.body.state;
    completedSteps = 1;
    const copy = SCENARIO_COPY[selectedScenario];
    $("request-detail").hidden = false;
    $("request-text").textContent = copy.request;
    $("request-date").textContent = copy.date;
    $("request-copy").textContent = copy.shown;
    showResult("info", "Request shown", "The demo request is ready for a local mock Check.");
    render();
  } catch (error) {
    lastResponse = {error: "demo_error"};
    handleFailure(lastResponse);
  }
}

async function checkRequest() {
  if (!plan) return;
  try {
    const result = await apiCall("/api/mock/check", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({plan})
    });
    lastResponse = result.body;
    if (!result.ok) {
      handleFailure(result.body);
      return;
    }
    lifecycle = result.body.state;
    completedSteps = 2;
    showResult("success", "Check complete", "The safe demo check passed. The example is ready for confirmation.");
    render();
  } catch (error) {
    lastResponse = {error: "demo_error"};
    handleFailure(lastResponse);
  }
}

async function confirmExample() {
  if (!plan) return;
  try {
    const result = await apiCall("/api/mock/confirm", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({plan, plan_id: plan.plan_id})
    });
    lastResponse = result.body;
    if (!result.ok) {
      handleFailure(result.body);
      return;
    }
    confirmation = result.body.confirmation;
    lifecycle = result.body.state;
    completedSteps = 3;
    showResult("success", "Confirmation recorded", "The exact example is confirmed for the final mock step.");
    render();
  } catch (error) {
    lastResponse = {error: "demo_error"};
    handleFailure(lastResponse);
  }
}

async function simulateUpdate() {
  if (!confirmation) return;
  try {
    const result = await apiCall("/api/mock/update", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({plan: confirmation})
    });
    lastResponse = result.body;
    if (!result.ok) {
      handleFailure(result.body);
      return;
    }
    lifecycle = result.body.state;
    completedSteps = 4;
    showResult("success", "Demo complete", "The local simulation finished. No real leave or work entry was created.");
    render();
  } catch (error) {
    lastResponse = {error: "demo_error"};
    handleFailure(lastResponse);
  }
}

async function resetDemo() {
  try {
    const result = await apiCall("/api/mock/reset", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: "{}"
    });
    lastResponse = result.body;
  } catch (error) {
    lastResponse = {error: "demo_error"};
  }
  plan = null;
  confirmation = null;
  lifecycle = "not_started";
  completedSteps = 0;
  $("request-detail").hidden = true;
  $("request-copy").textContent = "Choose an example, then select “1. Show request”.";
  showResult("neutral", "Ready for a demo", "The local simulation has been reset.");
  render();
}

scenarioCards.forEach((card) => card.addEventListener("click", chooseScenario));
$("show-request").addEventListener("click", showRequest);
$("check-request").addEventListener("click", checkRequest);
$("confirm-example").addEventListener("click", confirmExample);
$("simulate-update").addEventListener("click", simulateUpdate);
$("reset-demo").addEventListener("click", resetDemo);
render();
</script>
</body>
</html>
"""


class SandboxError(ValueError):
    """Safe, controlled sandbox request failure."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


def _fail(code: str) -> None:
    raise SandboxError(code)


def _scenario_preview(scenario: str) -> dict[str, Any]:
    planned_date = SCENARIOS.get(scenario)
    if planned_date is None:
        _fail("invalid_scenario")
    preview: dict[str, Any] = copy.deepcopy(mock_demo._preview())
    preview["date_range"] = {"start": planned_date, "end": planned_date}
    preview["eligible_dates"] = [planned_date]
    preview["planned_dates"] = [planned_date]
    preview["eligible_date_details"] = [{"date": planned_date, "holiday": None}]
    monthly = preview["monthly_overview"][0]
    monthly["month"] = planned_date[:7]
    monthly["eligible_dates"] = [planned_date]
    monthly["planned_dates"] = [planned_date]
    return preview


def _error_code(error: BaseException) -> str:
    code = getattr(error, "code", None)
    if isinstance(code, str) and code:
        return code
    text = str(error)
    return text if text else "sandbox_error"


class SandboxState:
    """Owns only in-memory adapter state for one server process."""

    def __init__(self) -> None:
        self.adapter = mock_adapter.MockSapAdapter()
        self.active_scenario: str | None = None
        self.active_plan: dict[str, Any] | None = None
        self.lifecycle_state = "not_started"
        self.checked_plan_id: str | None = None
        self.last_error: str | None = None
    def _adapter_for_scenario(self, scenario: str) -> mock_adapter.MockSapAdapter:
        fixture = mock_adapter.load_mock_fixture()
        if scenario in {"locked", "released"}:
            target_date = SCENARIOS[scenario]
            fixture["entries"] = [
                entry for entry in fixture["entries"] if entry["date"] != target_date
            ]
        return mock_adapter.MockSapAdapter(fixture=fixture)

    def _mark_failure(self, error: BaseException) -> None:
        self.lifecycle_state = "failed"
        self.checked_plan_id = None
        self.last_error = _error_code(error)

    def _require_active(self, plan: Any, state: str) -> dict[str, Any]:
        if type(plan) is not dict or self.active_plan is None:
            _fail("stale_plan")
        if plan.get("plan_id") != self.active_plan.get("plan_id"):
            _fail("stale_plan")
        if plan.get("state") != state:
            _fail("invalid_state")
        return plan

    def plan(self, scenario: str) -> dict[str, Any]:
        preview = _scenario_preview(scenario)
        plan = contract.build_adapter_plan(preview)
        self.adapter = self._adapter_for_scenario(scenario)
        self.active_scenario = scenario
        self.active_plan = plan
        self.checked_plan_id = None
        self.lifecycle_state = plan["state"]
        return plan

    def state(self) -> dict[str, Any]:
        return {
            "mock_only": True,
            "label": MOCK_LABEL,
            "status": "ok",
            "state": self.lifecycle_state,
            "active_scenario": self.active_scenario,
            "last_error": self.last_error,
            "fixture_mutated": False,
            "discovery": self.adapter.discover_read_only(),
            "existing_entries": self.adapter.read_existing_entries(),
            "monthly_status": self.adapter.read_monthly_status(),
        }

    def check(self, plan: Any) -> dict[str, Any]:
        try:
            validated = self._require_active(plan, "previewed")
            result = self.adapter.check_row(validated)
        except (SandboxError, mock_adapter.MockAdapterError, contract.ContractError) as error:
            self._mark_failure(error)
            raise
        self.lifecycle_state = result["state"]
        self.checked_plan_id = validated["plan_id"]
        self.last_error = None
        return result

    def confirm(self, plan: Any, plan_id: Any) -> dict[str, Any]:
        try:
            validated = self._require_active(plan, "previewed")
            if (
                self.lifecycle_state != "mock_checked"
                or self.checked_plan_id != validated["plan_id"]
                or validated != self.active_plan
            ):
                _fail("check_required")
            result = contract.confirm_adapter_plan(validated, plan_id)
            if result["state"] == "failed":
                _fail(result["error"])
        except (SandboxError, mock_adapter.MockAdapterError, contract.ContractError) as error:
            self._mark_failure(error)
            raise
        self.lifecycle_state = result["state"]
        self.last_error = None
        return result

    def update(self, confirmation: Any) -> dict[str, Any]:
        try:
            if self.lifecycle_state != "awaiting_confirmation":
                _fail("invalid_state")
            validated = self._require_active(confirmation, "awaiting_confirmation")
            result = self.adapter.update_one_row(validated)
        except (SandboxError, mock_adapter.MockAdapterError, contract.ContractError) as error:
            self._mark_failure(error)
            raise
        self.lifecycle_state = result["state"]
        self.last_error = None
        return result

    def reset(self) -> dict[str, Any]:
        self.adapter = mock_adapter.MockSapAdapter()
        self.active_scenario = None
        self.active_plan = None
        self.checked_plan_id = None
        self.lifecycle_state = "not_started"
        self.last_error = None
        return self.state()


def _strict_object(payload: Any, keys: set[str]) -> dict[str, Any]:
    if type(payload) is not dict or set(payload) != keys:
        _fail("invalid_request")
    return payload


def _read_json(handler: BaseHTTPRequestHandler) -> dict[str, Any]:
    raw_length = handler.headers.get("Content-Length", "0")
    try:
        length = int(raw_length)
    except ValueError:
        _fail("invalid_request")
    if length < 0 or length > 1_000_000:
        _fail("invalid_request")
    raw = handler.rfile.read(length)
    if not raw:
        return {}
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        _fail("invalid_json")
    if type(payload) is not dict:
        _fail("invalid_request")
    return payload


def _scenario_from_path(path: str) -> str:
    if "?" not in path:
        _fail("invalid_scenario")
    query = path.split("?", 1)[1]
    for item in query.split("&"):
        key, separator, value = item.partition("=")
        if separator and key == "scenario":
            return value
    _fail("invalid_scenario")


class SandboxHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.0"

    @property
    def sandbox(self) -> SandboxState:
        return self.server.sandbox  # type: ignore[attr-defined]

    def log_message(self, format: str, *args: Any) -> None:
        return

    def _write(self, status: int, payload: dict[str, Any], content_type: str = "application/json") -> None:
        body = (
            payload
            if content_type == "text/html"
            else json.dumps(payload, ensure_ascii=False, sort_keys=True)
        )
        encoded = body.encode("utf-8") if isinstance(body, str) else json.dumps(body).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", f"{content_type}; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def _failure(self, error: BaseException, status: int = 400) -> None:
        code = _error_code(error)
        if code in {"duplicate", "locked", "released", "plan_changed", "stale_plan", "stale_confirmation"}:
            status = 409
        self._write(
            status,
            {
                "mock_only": True,
                "label": MOCK_LABEL,
                "status": "failed",
                "state": "failed",
                "error": code,
                "fixture_mutated": False,
            },
        )

    def do_GET(self) -> None:
        path = self.path.split("?", 1)[0]
        try:
            if path == "/":
                self._write(200, HTML, "text/html")
                return
            if path == "/api/mock/state":
                self._write(200, self.sandbox.state())
                return
            if path == "/api/mock/plan":
                scenario = _scenario_from_path(self.path)
                plan = self.sandbox.plan(scenario)
                self._write(
                    200,
                    {
                        "mock_only": True,
                        "label": MOCK_LABEL,
                        "status": "ok",
                        "scenario": scenario,
                        "state": plan["state"],
                        "plan": plan,
                        "fixture_mutated": False,
                    },
                )
                return
            _fail("not_found")
        except (SandboxError, mock_adapter.MockAdapterError, contract.ContractError) as error:
            self._failure(error, 404 if _error_code(error) == "not_found" else 400)

    def do_POST(self) -> None:
        path = self.path.split("?", 1)[0]
        try:
            payload = _read_json(self)
            if path == "/api/mock/check":
                body = _strict_object(payload, {"plan"})
                result = self.sandbox.check(body["plan"])
                self._write(200, {"mock_only": True, "label": MOCK_LABEL, **result, "fixture_mutated": False})
                return
            if path == "/api/mock/confirm":
                body = _strict_object(payload, {"plan", "plan_id"})
                result = self.sandbox.confirm(body["plan"], body["plan_id"])
                self._write(
                    200,
                    {
                        "mock_only": True,
                        "label": MOCK_LABEL,
                        "status": "ok",
                        "state": result["state"],
                        "confirmation": result,
                        "fixture_mutated": False,
                    },
                )
                return
            if path == "/api/mock/update":
                body = _strict_object(payload, {"plan"})
                result = self.sandbox.update(body["plan"])
                self._write(200, {"mock_only": True, "label": MOCK_LABEL, **result})
                return
            if path == "/api/mock/reset":
                _strict_object(payload, set())
                self._write(200, self.sandbox.reset())
                return
            _fail("not_found")
        except (SandboxError, mock_adapter.MockAdapterError, contract.ContractError) as error:
            self._failure(error, 404 if _error_code(error) == "not_found" else 400)


class SandboxServer(HTTPServer):
    allow_reuse_address = True

    def __init__(self, address: tuple[str, int]) -> None:
        if address[0] != HOST:
            raise ValueError("sandbox must bind to 127.0.0.1")
        super().__init__(address, SandboxHandler)
        self.sandbox = SandboxState()


def make_server(port: int = 0) -> SandboxServer:
    """Create a local-only sandbox server without starting it."""
    return SandboxServer((HOST, port))


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Run the local MOCK ONLY sandbox")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    args = parser.parse_args()
    server = make_server(args.port)
    print(f"{MOCK_LABEL}: local sandbox listening on http://{HOST}:{server.server_port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        return 0
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
