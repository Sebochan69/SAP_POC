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
<head><meta charset="utf-8"><title>MOCK ONLY sandbox</title></head>
<body>
<h1>MOCK ONLY: local sandbox</h1>
<p>This is a deterministic local simulation, not connected to SAP.</p>
<label>Scenario
<select id="scenario">
<option value="safe">safe</option>
<option value="duplicate">duplicate</option>
<option value="locked">locked</option>
<option value="released">released</option>
</select>
</label>
<button id="plan">Load plan</button>
<button id="check">Check</button>
<button id="confirm">Confirm exact plan</button>
<button id="update">Mock update one row</button>
<button id="reset">Reset</button>
<pre id="output">Select a scenario.</pre>
<script>
let plan = null;
let confirmation = null;
const output = document.getElementById("output");
const scenario = document.getElementById("scenario");
async function call(path, options) {
  const response = await fetch(path, options);
  const body = await response.json();
  output.textContent = JSON.stringify(body, null, 2);
  return body;
}
async function loadPlan() {
  const body = await call(`/api/mock/plan?scenario=${scenario.value}`);
  plan = body.plan || null;
  confirmation = null;
}
document.getElementById("plan").onclick = loadPlan;
document.getElementById("check").onclick = async () => {
  if (plan) await call("/api/mock/check", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({plan})});
};
document.getElementById("confirm").onclick = async () => {
  if (plan) {
    confirmation = await call("/api/mock/confirm", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({plan, plan_id: plan.plan_id})});
    confirmation = confirmation.confirmation || null;
  }
};
document.getElementById("update").onclick = async () => {
  if (confirmation) await call("/api/mock/update", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({plan: confirmation})});
};
document.getElementById("reset").onclick = async () => {
  const body = await call("/api/mock/reset", {method: "POST", headers: {"Content-Type": "application/json"}, body: "{}"});
  plan = null;
  confirmation = null;
};
loadPlan();
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
