"""Runnable local mock lifecycle demonstration."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import integration_contract as contract
import mock_adapter


def _preview() -> dict[str, object]:
    planned_date = "2026-07-15"
    return {
        "dry_run": True,
        "kind": "preview",
        "request_kind": "leave",
        "date_range": {"start": planned_date, "end": planned_date},
        "leave_type": "sickness",
        "sap_code": "0200",
        "duration": {"kind": "full_day", "hours": None},
        "eligible_dates": [planned_date],
        "planned_dates": [planned_date],
        "eligible_date_details": [{"date": planned_date, "holiday": None}],
        "skipped_dates": [],
        "holiday_calendar": {
            "name": "Philippine national holidays 2026",
            "year": 2026,
            "source": {
                "title": "Proclamation No. 1006, s. 2025",
                "url": "local-fixture://philippine-holidays-2026",
                "revision_date": "2025-09-25",
                "live_validated": False,
                "note": "Local in-memory demo metadata; no runtime synchronization.",
            },
        },
        "existing_entries": {
            "configured": False,
            "name": None,
            "year": None,
            "source": {"kind": "none", "note": "No existing-entry snapshot is used by this demo."},
            "entry_count": 0,
        },
        "monthly_overview": [
            {
                "month": "2026-07",
                "eligible_dates": [planned_date],
                "planned_dates": [planned_date],
                "full_day_count": 1,
                "partial_day_hours": 0,
                "skipped_weekends": 0,
                "skipped_non_working_holidays": 0,
                "skipped_existing_entries": 0,
                "locked_status": "unavailable_in_dry_run",
                "release_status": "unavailable_in_dry_run",
                "warnings": [contract.DRY_RUN_WARNING],
            }
        ],
        "work_entries": [],
        "warnings": [contract.DRY_RUN_WARNING, contract.LOCAL_HOLIDAY_WARNING],
        "clarifications": [],
    }


def main() -> int:
    fixture_path = mock_adapter.DEFAULT_MOCK_FIXTURE_PATH
    fixture_before = fixture_path.read_bytes()
    fixture_hash_before = hashlib.sha256(fixture_before).hexdigest()
    adapter = mock_adapter.MockSapAdapter()
    adapter_fixture_before = adapter.fixture

    plan = contract.build_adapter_plan(_preview())
    discovery = adapter.discover_read_only()
    checked = adapter.check_row(plan)
    confirmation = contract.confirm_adapter_plan(plan, plan["plan_id"])
    updated = adapter.update_one_row(confirmation)

    fixture_after = fixture_path.read_bytes()
    fixture_mutated = (
        fixture_before != fixture_after
        or hashlib.sha256(fixture_after).hexdigest() != fixture_hash_before
        or adapter.fixture != adapter_fixture_before
        or updated.get("fixture_mutated") is not False
    )
    if fixture_mutated:
        raise RuntimeError("mock fixture mutated")

    result = {
        "demo": "Feature 6D local mock lifecycle",
        "label": "MOCK ONLY",
        "warning": discovery["warnings"][0],
        "mock_only": discovery["mock_only"],
        "states": {
            "plan": plan["state"],
            "check": checked["state"],
            "confirmation": confirmation["state"],
            "update": updated["state"],
        },
        "fixture_mutated": False,
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
