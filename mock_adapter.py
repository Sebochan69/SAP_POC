"""Feature 6C local mock-only adapter.

This module is a deterministic in-memory POC seam. It does not represent live
SAP behavior and intentionally has no browser, network, credential, or
submission integration.
"""

from __future__ import annotations

import copy
import json
import math
import re
from datetime import date
from pathlib import Path
from typing import Any

import integration_contract as contract

DEFAULT_MOCK_FIXTURE_PATH = Path(__file__).with_name("config") / "mock_sap_2026.json"
MOCK_ONLY_WARNING = "MOCK ONLY: local fixture simulation; not connected to SAP."
MOCK_IDENTITY_RULE = "date"
DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")
MONTH_PATTERN = re.compile(r"^\d{4}-\d{2}$")
FIXTURE_KEYS = frozenset({"kind", "name", "year", "entries", "monthly_status"})
ENTRY_KEYS = frozenset(
    {
        "date",
        "entry_kind",
        "leave_code",
        "favorite_code",
        "hours_per_day",
        "billable",
        "task_description",
        "state",
    }
)
MONTH_STATUS_KEYS = frozenset({"month", "locked_status", "release_status"})
ENTRY_KINDS = frozenset({"leave", "work"})
ENTRY_STATES = frozenset({"booked", "draft", "locked", "released", "mock_submitted"})
LEAVE_CODES = frozenset({"0200", "0600"})
LOCKED_STATES = frozenset({"locked"})
RELEASED_STATES = frozenset({"released"})
LOCKED_STATUS_VALUES = frozenset({"locked", "unlocked"})
RELEASE_STATUS_VALUES = frozenset({"released", "unreleased"})


class MockAdapterError(ValueError):
    """A fail-closed mock fixture, plan, or action error."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


def _fail(code: str) -> None:
    raise MockAdapterError(code)


def _non_empty_string(value: Any, code: str) -> str:
    if not isinstance(value, str) or not value.strip():
        _fail(code)
    return value.strip()


def _date_value(value: Any, year: int, code: str = "invalid_fixture_date") -> str:
    if not isinstance(value, str) or DATE_PATTERN.fullmatch(value) is None:
        _fail(code)
    try:
        parsed = date.fromisoformat(value)
    except ValueError:
        _fail(code)
    if parsed.year != year:
        _fail(code)
    return value


def _month_value(value: Any, year: int) -> str:
    if not isinstance(value, str) or MONTH_PATTERN.fullmatch(value) is None:
        _fail("invalid_fixture_month")
    month_year, month = value.split("-")
    if int(month_year) != year or not 1 <= int(month) <= 12:
        _fail("invalid_fixture_month")
    return value


def _number_or_none(value: Any, code: str) -> int | float | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        _fail(code)
    try:
        finite = math.isfinite(value)
    except OverflowError:
        finite = False
    if not finite or value <= 0 or value > 24:
        _fail(code)
    return value


def _validate_entry(entry: Any, year: int) -> dict[str, Any]:
    if type(entry) is not dict or set(entry) != ENTRY_KEYS:
        _fail("invalid_fixture_entry")
    entry_date = _date_value(entry["date"], year)
    entry_kind = entry["entry_kind"]
    if not isinstance(entry_kind, str) or entry_kind not in ENTRY_KINDS:
        _fail("invalid_fixture_entry_kind")
    state = entry["state"]
    if not isinstance(state, str) or state not in ENTRY_STATES - {"mock_submitted"}:
        _fail("invalid_fixture_state")
    leave_code = entry["leave_code"]
    favorite_code = entry["favorite_code"]
    hours_per_day = entry["hours_per_day"]
    billable = entry["billable"]
    task_description = entry["task_description"]
    if entry_kind == "leave":
        if not isinstance(leave_code, str) or leave_code not in LEAVE_CODES:
            _fail("invalid_fixture_entry")
        if any(value is not None for value in (favorite_code, hours_per_day, billable, task_description)):
            _fail("invalid_fixture_entry")
    else:
        if leave_code is not None:
            _fail("invalid_fixture_entry")
        _non_empty_string(favorite_code, "invalid_fixture_entry")
        hours = _number_or_none(hours_per_day, "invalid_fixture_entry")
        if hours is None:
            _fail("invalid_fixture_entry")
        if type(billable) is not bool:
            _fail("invalid_fixture_entry")
        _non_empty_string(task_description, "invalid_fixture_entry")
    return copy.deepcopy(entry) | {"date": entry_date}

def validate_mock_fixture(value: Any) -> dict[str, Any]:
    """Validate and copy a Feature 6C fixture; never mutate the input."""
    if type(value) is not dict or set(value) != FIXTURE_KEYS:
        _fail("invalid_fixture")
    if value["kind"] != "mock_sap_fixture":
        _fail("invalid_fixture_kind")
    name = _non_empty_string(value["name"], "invalid_fixture")
    year = value["year"]
    if type(year) is not int or not 1_000 <= year <= 9_999:
        _fail("invalid_fixture_year")
    entries = value["entries"]
    if type(entries) is not list:
        _fail("invalid_fixture_entries")
    validated_entries: list[dict[str, Any]] = []
    seen_dates: set[str] = set()
    for entry in entries:
        validated = _validate_entry(entry, year)
        if validated["date"] in seen_dates:
            # Date is the documented mock identity. A duplicate is ambiguous.
            _fail("duplicate_fixture_date")
        seen_dates.add(validated["date"])
        validated_entries.append(validated)
    monthly_status = value["monthly_status"]
    if type(monthly_status) is not list:
        _fail("invalid_monthly_status")
    validated_status: list[dict[str, Any]] = []
    seen_months: set[str] = set()
    for item in monthly_status:
        if type(item) is not dict or set(item) != MONTH_STATUS_KEYS:
            _fail("invalid_monthly_status")
        month = _month_value(item["month"], year)
        if month in seen_months:
            _fail("duplicate_fixture_month")
        seen_months.add(month)
        locked_status = item["locked_status"]
        release_status = item["release_status"]
        if not isinstance(locked_status, str) or locked_status not in LOCKED_STATUS_VALUES:
            _fail("invalid_lock_status")
        if not isinstance(release_status, str) or release_status not in RELEASE_STATUS_VALUES:
            _fail("invalid_release_status")
        validated_status.append(copy.deepcopy(item) | {"month": month})
    validated_status.sort(key=lambda item: item["month"])
    validated_entries.sort(key=lambda item: item["date"])
    return {
        "kind": value["kind"],
        "name": name,
        "year": year,
        "entries": validated_entries,
        "monthly_status": validated_status,
    }


def load_mock_fixture(path: str | Path = DEFAULT_MOCK_FIXTURE_PATH) -> dict[str, Any]:
    """Load one local JSON fixture and return its validated copy."""
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise MockAdapterError("invalid_fixture") from error
    return validate_mock_fixture(value)


def _range_bounds(start: Any, end: Any) -> tuple[str | None, str | None]:
    if isinstance(start, dict) and end is None:
        if set(start) != {"start", "end"}:
            _fail("invalid_date_range")
        end = start["end"]
        start = start["start"]
    if start is None and end is None:
        return None, None
    if not isinstance(start, str) or not isinstance(end, str):
        _fail("invalid_date_range")
    if DATE_PATTERN.fullmatch(start) is None or DATE_PATTERN.fullmatch(end) is None:
        _fail("invalid_date_range")
    parsed_start = _date_value(start, int(start[:4]), "invalid_date_range")
    parsed_end = _date_value(end, int(end[:4]), "invalid_date_range")
    if parsed_start > parsed_end:
        _fail("invalid_date_range")
    return parsed_start, parsed_end


class MockSapAdapter:
    """Clearly marked Feature 6C mock-only lifecycle adapter.

    The identity rule is intentionally mock behavior, not SAP truth: a planned
    row conflicts with an existing row when its date matches. The fixture is
    loaded once and never written; simulated updates modify only an in-memory
    copy and require a checked row plus an exact Feature 6A confirmation result.
    """

    mock_only = True

    def __init__(
        self,
        fixture_path: str | Path = DEFAULT_MOCK_FIXTURE_PATH,
        *,
        fixture: Any | None = None,
    ) -> None:
        if fixture is not None:
            self._fixture = validate_mock_fixture(fixture)
            self.fixture_path: Path | None = None
        else:
            self._fixture = load_mock_fixture(fixture_path)
            self.fixture_path = Path(fixture_path)
        self._entries = copy.deepcopy(self._fixture["entries"])
        self._monthly_status = copy.deepcopy(self._fixture["monthly_status"])
        self._checked: set[tuple[str, int]] = set()
        self._aborted = False

    @property
    def fixture(self) -> dict[str, Any]:
        """Return a copy; the loaded fixture and source file remain immutable."""
        return copy.deepcopy(self._fixture)

    def _ensure_active(self) -> None:
        if self._aborted:
            _fail("aborted")

    def discover_read_only(self) -> dict[str, Any]:
        return {
            "mock_only": True,
            "status": "ok",
            "source": "mock_fixture",
            "identity_rule": MOCK_IDENTITY_RULE,
            "year": self._fixture["year"],
            "operations": ["read", "check", "confirm", "one_row_mock_update", "abort"],
            "evidence_ref": "mock_evidence:discovery",
            "warnings": [MOCK_ONLY_WARNING],
        }

    def _redacted_entry(self, entry: dict[str, Any]) -> dict[str, Any]:
        return {
            "date": entry["date"],
            "entry_kind": entry["entry_kind"],
            "leave_code": entry["leave_code"],
            "favorite_code": "mock_redacted" if entry["favorite_code"] is not None else None,
            "hours_per_day": entry["hours_per_day"],
            "billable": entry["billable"],
            "task_description_present": entry["task_description"] is not None,
            "row_identity": f"mock-date:{entry['date']}",
            "state": entry["state"],
        }

    def read_existing_entries(
        self, start: str | dict[str, str] | None = None, end: str | None = None
    ) -> dict[str, Any]:
        start, end = _range_bounds(start, end)
        entries = [
            self._redacted_entry(entry)
            for entry in self._entries
            if (start is None or start <= entry["date"] <= end)
        ]
        return {
            "mock_only": True,
            "status": "ok",
            "source": "mock_fixture",
            "entries": entries,
            "evidence_ref": "mock_evidence:existing_entries",
            "warnings": [MOCK_ONLY_WARNING],
        }

    def read_monthly_status(
        self, start: str | dict[str, str] | None = None, end: str | None = None
    ) -> dict[str, Any]:
        start, end = _range_bounds(start, end)
        start_month = start[:7] if start is not None else None
        end_month = end[:7] if end is not None else None
        months: list[dict[str, Any]] = []
        for status in self._monthly_status:
            month = status["month"]
            if start_month is not None and not start_month <= month <= end_month:
                continue
            month_entries = [entry for entry in self._entries if entry["date"].startswith(month)]
            months.append(
                {
                    "month": month,
                    "planned_count": None,
                    "existing_count": len(month_entries),
                    "total_hours": sum(
                        entry["hours_per_day"] or 0
                        for entry in month_entries
                        if entry["entry_kind"] == "work"
                    ),
                    "locked_status": status["locked_status"],
                    "release_status": status["release_status"],
                    "evidence_ref": f"mock_evidence:monthly:{month}",
                }
            )
        return {
            "mock_only": True,
            "status": "ok",
            "source": "mock_fixture",
            "months": months,
            "evidence_ref": "mock_evidence:monthly_status",
            "warnings": [MOCK_ONLY_WARNING],
        }

    def _validated_plan(self, plan: Any, state: str) -> dict[str, Any]:
        if type(plan) is not dict or plan.get("state") != state:
            _fail("invalid_plan")
        candidate = copy.deepcopy(plan)
        if state == "previewed":
            try:
                confirmed = contract.confirm_adapter_plan(candidate, candidate.get("plan_id"))
            except contract.ContractError as error:
                raise MockAdapterError("stale_plan") from error
            if confirmed.get("state") != "awaiting_confirmation":
                _fail("stale_plan")
        else:
            previewed = copy.deepcopy(candidate)
            previewed["state"] = "previewed"
            try:
                confirmed = contract.confirm_adapter_plan(previewed, previewed.get("plan_id"))
            except contract.ContractError as error:
                raise MockAdapterError("stale_confirmation") from error
            if confirmed != candidate:
                _fail("stale_confirmation")
        return candidate

    def _row(self, plan: dict[str, Any], row_index: int) -> dict[str, Any]:
        if isinstance(row_index, bool) or not isinstance(row_index, int):
            _fail("invalid_row")
        rows = plan["planned_rows"]
        if not 0 <= row_index < len(rows):
            _fail("invalid_row")
        return rows[row_index]

    def _evaluate_row(self, row: dict[str, Any]) -> None:
        matches = [entry for entry in self._entries if entry["date"] == row["date"]]
        if len(matches) > 1:
            _fail("ambiguous")
        if matches:
            _fail("duplicate")
        status = next(
            (item for item in self._monthly_status if item["month"] == row["date"][:7]),
            None,
        )
        if status is None:
            _fail("ambiguous")
        if status["locked_status"] == "locked":
            _fail("locked")
        if status["locked_status"] != "unlocked":
            _fail("ambiguous")
        if status["release_status"] == "released":
            _fail("released")
        if status["release_status"] != "unreleased":
            _fail("ambiguous")

    def check_row(self, plan: Any, row_index: int = 0) -> dict[str, Any]:
        self._ensure_active()
        validated = self._validated_plan(plan, "previewed")
        row = self._row(validated, row_index)
        self._evaluate_row(row)
        self._checked.add((validated["plan_id"], row_index))
        return {
            "mock_only": True,
            "status": "ok",
            "state": "mock_checked",
            "row_index": row_index,
            "date": row["date"],
            "evidence_ref": f"mock_evidence:check:{row['date']}",
            "warnings": [MOCK_ONLY_WARNING],
        }

    def update_one_row(
        self,
        plan_or_confirmation: Any,
        confirmation: Any | None = None,
        row_index: int = 0,
    ) -> dict[str, Any]:
        self._ensure_active()
        if confirmation is None:
            confirmation = plan_or_confirmation
            if type(confirmation) is not dict or confirmation.get("state") != "awaiting_confirmation":
                _fail("stale_confirmation")
            plan = copy.deepcopy(confirmation)
            plan["state"] = "previewed"
        else:
            plan = plan_or_confirmation
        validated_plan = self._validated_plan(plan, "previewed")
        validated_confirmation = self._validated_plan(confirmation, "awaiting_confirmation")
        expected_confirmation = copy.deepcopy(validated_plan)
        expected_confirmation["state"] = "awaiting_confirmation"
        if validated_confirmation != expected_confirmation:
            _fail("stale_confirmation")
        if len(validated_plan["planned_rows"]) != 1:
            _fail("one_row_only")
        row = self._row(validated_plan, row_index)
        if (validated_plan["plan_id"], row_index) not in self._checked:
            _fail("check_required")
        self._evaluate_row(row)
        self._entries.append(
            {
                "date": row["date"],
                "entry_kind": row["request_kind"],
                "leave_code": row.get("sap_code"),
                "favorite_code": row.get("favorite_code"),
                "hours_per_day": row.get("hours_per_day"),
                "billable": row.get("billable"),
                "task_description": row.get("task_description"),
                "state": "mock_submitted",
            }
        )
        return {
            "mock_only": True,
            "status": "mock_submitted",
            "state": "mock_submitted",
            "fixture_mutated": False,
            "row": {
                "date": row["date"],
                "entry_kind": row["request_kind"],
                "row_identity": f"mock-date:{row['date']}",
            },
            "evidence_ref": f"mock_evidence:update:{row['date']}",
            "warnings": [MOCK_ONLY_WARNING],
        }

    def update_row(
        self,
        plan_or_confirmation: Any,
        confirmation: Any | None = None,
        row_index: int = 0,
    ) -> dict[str, Any]:
        return self.update_one_row(plan_or_confirmation, confirmation, row_index)

    def abort(self) -> dict[str, Any]:
        self._aborted = True
        return {
            "mock_only": True,
            "status": "mock_aborted",
            "state": "mock_aborted",
            "updates_allowed": False,
            "evidence_ref": "mock_evidence:abort",
            "warnings": [MOCK_ONLY_WARNING],
        }

    def kill_switch(self) -> dict[str, Any]:
        return self.abort()
