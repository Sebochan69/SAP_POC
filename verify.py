from __future__ import annotations

import http.client
import json
import tempfile
import threading
import unittest
from unittest import mock
from pathlib import Path
from typing import Any

import app
import integration_contract as contract


class FakeOllama:
    def __init__(self, response: Any) -> None:
        self.response = response
        self.requests: list[str] = []

    def extract(self, user_text: str) -> Any:
        self.requests.append(user_text)
        return self.response


def intent(
    start: str | None,
    leave_type: str,
    duration_kind: str,
    hours: int | float | None = None,
    end: str | None = None,
    request_kind: str = "leave",
    work: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if work is None:
        work = {
            "favorite_code": None,
            "hours_per_day": None,
            "billable": None,
            "task_description": None,
        }
    return {
        "request_kind": request_kind,
        "date_range": {"start": start, "end": start if end is None else end},
        "leave_type": leave_type,
        "duration": {"kind": duration_kind, "hours": hours},
        "work": work,
    }


def existing_snapshot(*dates: str) -> dict[str, Any]:
    return {
        "name": "Local existing entries 2026",
        "year": 2026,
        "source": {"kind": "local_fixture", "note": "Not connected to SAP"},
        "entries": [{"date": entry_date, "label": "existing entry"} for entry_date in dates],
    }


def work_intent(
    start: str | None,
    favorite_code: str | None = "WBS-42",
    hours_per_day: int | float | None = 6,
    billable: bool | None = True,
    task_description: str | None = "Implementation",
    end: str | None = None,
    request_kind: str = "work",
) -> dict[str, Any]:
    return intent(
        start,
        "unknown",
        "unspecified",
        None,
        end,
        request_kind,
        {
            "favorite_code": favorite_code,
            "hours_per_day": hours_per_day,
            "billable": billable,
            "task_description": task_description,
        },
    )


def rehashed_plan(plan: dict[str, Any]) -> dict[str, Any]:
    result = json.loads(json.dumps(plan))
    data = {
        key: result[key]
        for key in (
            "request_kind",
            "date_range",
            "planned_rows",
            "calendar_summary",
            "existing_summary",
            "monthly_summary",
            "skip_summary",
            "warnings",
        )
    }
    result["plan_id"] = contract._plan_id(data)
    return result



class FeatureVerification(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.log_path = Path(self.temp_dir.name) / "events.jsonl"

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def preview(
        self,
        model_response: Any,
        text: str,
        existing_snapshot: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return app.build_preview(
            text,
            FakeOllama(model_response),
            app.JsonlLogger(self.log_path),
            existing_snapshot=existing_snapshot,
        )

    def test_sickness_maps_to_0200(self) -> None:
        result = self.preview(
            intent("2026-07-15", "sickness", "full_day"),
            "I was sick on July 15, 2026",
        )
        self.assertEqual(result["kind"], "preview")
        self.assertEqual(result["sap_code"], "0200")
        self.assertEqual(result["date_range"], {"start": "2026-07-15", "end": "2026-07-15"})
        self.assertTrue(result["dry_run"])

    def test_paid_leave_maps_to_0600(self) -> None:
        result = self.preview(
            intent("2026-07-15", "paid_leave", "hours", 4),
            "I need four hours of paid leave on July 15, 2026",
        )
        self.assertEqual(result["kind"], "preview")
        self.assertEqual(result["sap_code"], "0600")
        self.assertEqual(result["duration"], {"kind": "hours", "hours": 4})

    def test_ambiguous_leave_type_requests_clarification(self) -> None:
        result = self.preview(
            intent("2026-07-15", "unknown", "full_day"),
            "I will be on leave on July 15, 2026",
        )
        self.assertEqual(result["kind"], "clarification")
        self.assertIsNone(result["sap_code"])
        self.assertIn("0200", result["clarifications"][0])
        self.assertIn("0600", result["clarifications"][0])

    def test_missing_duration_requests_clarification(self) -> None:
        result = self.preview(
            intent("2026-07-15", "sickness", "unspecified"),
            "I was sick on July 15, 2026",
        )
        self.assertEqual(result["kind"], "clarification")
        self.assertIn("full day", result["clarifications"][0])

    def test_invalid_model_output_is_rejected(self) -> None:
        malformed = intent("2026-07-15", "sickness", "full_day")
        malformed["unexpected"] = "reject me"
        with self.assertRaisesRegex(app.ValidationError, "invalid_model_schema"):
            self.preview(malformed, "I was sick on July 15, 2026")

    def test_logs_are_jsonl_and_do_not_contain_raw_user_text(self) -> None:
        raw_text = "I was sick on July 15, 2026; token=do-not-log"
        self.preview(intent("2026-07-15", "sickness", "full_day"), raw_text)
        log_text = self.log_path.read_text(encoding="utf-8")
        self.assertNotIn(raw_text, log_text)
        self.assertNotIn("do-not-log", log_text)
        records = [json.loads(line) for line in log_text.splitlines()]
        self.assertEqual([record["stage"] for record in records], ["parse", "parse", "validate", "preview"])
        self.assertTrue(all(set(record) == {"timestamp", "stage", "outcome", "fields"} for record in records))

    def test_april_range_leaves_only_april_6_eligible(self) -> None:
        result = self.preview(
            intent("2026-04-02", "sickness", "full_day", end="2026-04-06"),
            "I was sick from April 2 to April 6, 2026",
        )
        self.assertEqual(result["kind"], "preview")
        self.assertEqual(result["eligible_dates"], ["2026-04-06"])
        skipped = {item["date"]: item for item in result["skipped_dates"]}
        self.assertEqual(skipped["2026-04-02"]["reason"], "holiday")
        self.assertEqual(skipped["2026-04-02"]["holiday"]["category"], "regular_holiday")
        self.assertEqual(skipped["2026-04-04"]["reason"], "weekend")
        self.assertEqual(skipped["2026-04-04"]["holiday"]["category"], "special_non_working")
        self.assertEqual(skipped["2026-04-05"]["reason"], "weekend")

    def test_august_21_is_special_non_working(self) -> None:
        result = self.preview(
            intent("2026-08-21", "sickness", "full_day"),
            "I was sick on August 21, 2026",
        )
        self.assertEqual(result["kind"], "clarification")
        self.assertEqual(result["eligible_dates"], [])
        self.assertEqual(result["skipped_dates"][0]["reason"], "holiday")
        self.assertEqual(result["skipped_dates"][0]["holiday"]["name"], "Ninoy Aquino Day")
        self.assertIn("No eligible weekday", result["clarifications"][-1])

    def test_february_25_special_working_remains_eligible(self) -> None:
        result = self.preview(
            intent("2026-02-25", "paid_leave", "full_day"),
            "I need paid leave on February 25, 2026",
        )
        self.assertEqual(result["kind"], "preview")
        self.assertEqual(result["eligible_dates"], ["2026-02-25"])
        self.assertEqual(
            result["eligible_date_details"][0]["holiday"]["category"],
            "special_working",
        )
        self.assertEqual(result["skipped_dates"], [])

    def test_contract_rejects_dates_outside_preview_range(self) -> None:
        leave = self.preview(
            intent("2026-07-15", "sickness", "full_day"),
            "I was sick on July 15, 2026",
        )
        for field in ("planned_dates", "eligible_dates"):
            malformed = json.loads(json.dumps(leave))
            malformed[field] = ["2026-07-16"]
            with self.assertRaises(contract.ContractError):
                contract.build_adapter_plan(malformed)

        malformed_detail = json.loads(json.dumps(leave))
        malformed_detail["eligible_date_details"][0]["date"] = "2026-07-16"
        with self.assertRaises(contract.ContractError):
            contract.build_adapter_plan(malformed_detail)

        work = self.preview(work_intent("2026-07-30"), "Work on July 30, 2026")
        malformed_work = json.loads(json.dumps(work))
        malformed_work["work_entries"][0]["date"] = "2026-07-31"
        with self.assertRaises(contract.ContractError):
            contract.build_adapter_plan(malformed_work)

    def test_leave_unspecified_duration_is_rejected_without_clarification(self) -> None:
        malformed = self.preview(
            intent("2026-07-15", "sickness", "full_day"),
            "I was sick on July 15, 2026",
        )
        malformed["duration"] = {"kind": "unspecified", "hours": None}
        with self.assertRaises(contract.ContractError):
            contract.build_adapter_plan(malformed)

    def test_holiday_skip_requires_matching_non_working_holiday(self) -> None:
        preview = self.preview(
            intent("2026-08-20", "sickness", "full_day", end="2026-08-21"),
            "I was sick on August 20 and 21, 2026",
        )
        self.assertEqual(preview["kind"], "preview")
        for holiday in (None, {"date": "2026-08-21", "name": "wrong", "category": "special_working"}):
            malformed = json.loads(json.dumps(preview))
            malformed["skipped_dates"][0]["holiday"] = holiday
            with self.assertRaises(contract.ContractError):
                contract.build_adapter_plan(malformed)

    def test_range_with_no_eligible_date_is_clarified(self) -> None:
        result = self.preview(
            intent("2026-04-02", "sickness", "full_day", end="2026-04-05"),
            "I was sick from April 2 to April 5, 2026",
        )
        self.assertEqual(result["kind"], "clarification")
        self.assertEqual(result["eligible_dates"], [])
        self.assertIn("No eligible weekday", result["clarifications"][-1])

    def test_missing_year_is_not_guessed(self) -> None:
        result = self.preview(
            intent(None, "sickness", "full_day"),
            "I was sick from April 2 to April 6",
        )
        self.assertEqual(result["kind"], "clarification")
        self.assertIn("What date", result["clarifications"][0])


    def test_model_hallucinated_year_is_rejected_without_explicit_year(self) -> None:
        result = self.preview(
            intent("2024-08-20", "sickness", "full_day"),
            "i will take a leave on Aug 20",
        )
        self.assertEqual(result["kind"], "clarification")
        self.assertEqual(result["date_range"], {"start": None, "end": None})
        self.assertEqual(result["eligible_dates"], [])
        self.assertEqual(result["planned_dates"], [])
        self.assertIn("What date", result["clarifications"][0])

    def test_model_year_must_match_explicit_user_year(self) -> None:
        result = self.preview(
            intent("2024-08-20", "sickness", "full_day"),
            "I will take a leave on Aug 20, 2026",
        )
        self.assertEqual(result["kind"], "clarification")
        self.assertEqual(result["date_range"], {"start": None, "end": None})
        self.assertEqual(result["eligible_dates"], [])
        self.assertEqual(result["planned_dates"], [])
        self.assertIn("What date", result["clarifications"][0])

    def test_existing_date_is_removed_and_reported(self) -> None:
        snapshot = existing_snapshot("2026-07-15")
        result = self.preview(
            intent("2026-07-15", "sickness", "full_day"),
            "I was sick on July 15, 2026",
            snapshot,
        )
        self.assertEqual(result["kind"], "clarification")
        self.assertEqual(result["eligible_dates"], [])
        self.assertEqual(result["planned_dates"], [])
        skipped = result["skipped_dates"][0]
        self.assertEqual(skipped["reason"], "existing_entry")
        self.assertEqual(skipped["existing_entry"]["source"]["kind"], "local_fixture")
        self.assertEqual(result["existing_entries"]["entry_count"], 1)
        self.assertEqual(result["monthly_overview"][0]["skipped_existing_entries"], 1)
        self.assertNotIn("existing entry", self.log_path.read_text(encoding="utf-8"))

    def test_all_candidates_existing_produces_clarification(self) -> None:
        result = self.preview(
            intent("2026-07-15", "paid_leave", "hours", 4, end="2026-07-16"),
            "I need paid leave on July 15 and 16, 2026",
            existing_snapshot("2026-07-15", "2026-07-16"),
        )
        self.assertEqual(result["kind"], "clarification")
        self.assertEqual(result["planned_dates"], [])
        self.assertEqual(
            {item["reason"] for item in result["skipped_dates"]},
            {"existing_entry"},
        )
        self.assertIn("already have existing entries", result["clarifications"][-1])

    def test_monthly_overview_spans_two_months_and_counts_skips(self) -> None:
        result = self.preview(
            intent("2026-08-28", "sickness", "full_day", end="2026-09-02"),
            "I was sick from August 28 to September 2, 2026",
            existing_snapshot("2026-09-02"),
        )
        months = {item["month"]: item for item in result["monthly_overview"]}
        self.assertEqual(set(months), {"2026-08", "2026-09"})
        self.assertEqual(months["2026-08"]["planned_dates"], ["2026-08-28"])
        self.assertEqual(months["2026-08"]["skipped_weekends"], 2)
        self.assertEqual(months["2026-08"]["skipped_non_working_holidays"], 1)
        self.assertEqual(months["2026-09"]["planned_dates"], ["2026-09-01"])
        self.assertEqual(months["2026-09"]["skipped_existing_entries"], 1)
        self.assertEqual(months["2026-09"]["full_day_count"], 1)
        self.assertEqual(months["2026-09"]["partial_day_hours"], 0)
        self.assertEqual(months["2026-09"]["locked_status"], "unavailable_in_dry_run")
        self.assertEqual(months["2026-09"]["release_status"], "unavailable_in_dry_run")

    def test_monthly_overview_counts_explicit_hours_only(self) -> None:
        partial = self.preview(
            intent("2026-07-30", "sickness", "hours", 4, end="2026-07-31"),
            "I need four hours on July 30 and 31, 2026",
        )
        self.assertEqual(partial["monthly_overview"][0]["partial_day_hours"], 8)
        self.assertEqual(partial["monthly_overview"][0]["full_day_count"], 0)

        full_day = self.preview(
            intent("2026-07-30", "sickness", "full_day", end="2026-07-31"),
            "I was sick for two full days on July 30 and 31, 2026",
        )
        self.assertEqual(full_day["monthly_overview"][0]["full_day_count"], 2)
        self.assertEqual(full_day["monthly_overview"][0]["partial_day_hours"], 0)

    def test_existing_snapshot_validation_rejects_bad_files(self) -> None:
        malformed = {
            "name": "Local existing entries 2026",
            "year": 2026,
            "source": {"kind": "local_fixture", "note": "Not connected to SAP"},
        }
        duplicate_dates = existing_snapshot("2026-07-15", "2026-07-15")
        invalid_date = existing_snapshot("2026-07-32")
        for index, payload in enumerate((malformed, duplicate_dates, invalid_date)):
            path = Path(self.temp_dir.name) / f"snapshot-{index}.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "invalid_existing_entries"):
                app.load_existing_entries(path)

    def test_complete_work_request_produces_deterministic_entries(self) -> None:
        result = self.preview(
            work_intent(
                "2026-07-30",
                favorite_code="WBS-DEV-7",
                hours_per_day=6,
                billable=False,
                task_description="Implement the leave planner",
                end="2026-07-31",
            ),
            "Work on the leave planner July 30 and 31, 2026",
        )
        self.assertEqual(result["kind"], "preview")
        self.assertEqual(result["request_kind"], "work")
        self.assertEqual(result["sap_code"], None)
        self.assertEqual(
            result["work_entries"],
            [
                {
                    "date": "2026-07-30",
                    "favorite_code": "WBS-DEV-7",
                    "hours_per_day": 6,
                    "billable": False,
                    "task_description": "Implement the leave planner",
                },
                {
                    "date": "2026-07-31",
                    "favorite_code": "WBS-DEV-7",
                    "hours_per_day": 6,
                    "billable": False,
                    "task_description": "Implement the leave planner",
                },
            ],
        )
        self.assertEqual(result["monthly_overview"][0]["partial_day_hours"], 12)
        log_text = self.log_path.read_text(encoding="utf-8")
        self.assertNotIn("WBS-DEV-7", log_text)
        self.assertNotIn("Implement the leave planner", log_text)

    def test_work_uses_holiday_and_duplicate_filters(self) -> None:
        result = self.preview(
            work_intent("2026-04-01", end="2026-04-06"),
            "Work on the planner from April 1 to April 6, 2026",
            existing_snapshot("2026-04-06"),
        )
        self.assertEqual([entry["date"] for entry in result["work_entries"]], ["2026-04-01"])
        skipped = {item["date"]: item for item in result["skipped_dates"]}
        self.assertEqual(skipped["2026-04-02"]["holiday"]["category"], "regular_holiday")
        self.assertEqual(skipped["2026-04-04"]["reason"], "weekend")
        self.assertEqual(skipped["2026-04-06"]["reason"], "existing_entry")
        self.assertEqual(result["monthly_overview"][0]["skipped_existing_entries"], 1)

    def test_missing_work_fields_request_clarification_without_entries(self) -> None:
        cases = (
            ("favorite_code", "Favorite WBS/project code"),
            ("hours_per_day", "hours per day"),
            ("billable", "billable"),
            ("task_description", "task description"),
        )
        for field, expected in cases:
            with self.subTest(field=field):
                values = {
                    "favorite_code": "WBS-42",
                    "hours_per_day": 6,
                    "billable": True,
                    "task_description": "Implementation",
                }
                values[field] = None
                result = self.preview(
                    work_intent("2026-07-30", **values),
                    "I need to work on July 30, 2026",
                )
                self.assertEqual(result["kind"], "clarification")
                self.assertEqual(result["work_entries"], [])
                self.assertTrue(any(expected in message for message in result["clarifications"]))

    def test_work_missing_date_and_unknown_request_kind_are_clarified(self) -> None:
        missing_date = self.preview(
            work_intent(None),
            "Work on the planner from July 30 to July 31",
        )
        self.assertEqual(missing_date["kind"], "clarification")
        self.assertEqual(missing_date["work_entries"], [])
        self.assertIn("date", missing_date["clarifications"][0])

        unknown = self.preview(
            intent(
                "2026-07-30",
                "unknown",
                "unspecified",
                request_kind="unknown",
            ),
            "Do something on July 30, 2026",
        )
        self.assertEqual(unknown["kind"], "clarification")
        self.assertEqual(unknown["request_kind"], "unknown")
        self.assertIn("leave request or a work entry", unknown["clarifications"][0])
        self.assertEqual(unknown["work_entries"], [])

    def test_invalid_work_field_types_and_extra_keys_are_rejected(self) -> None:
        invalid_hours = work_intent("2026-07-30", hours_per_day="six")  # type: ignore[arg-type]
        invalid_billable = work_intent("2026-07-30", billable="yes")  # type: ignore[arg-type]
        extra_work_key = work_intent("2026-07-30")
        extra_work_key["work"]["unexpected"] = "reject"
        for response in (invalid_hours, invalid_billable, extra_work_key):
            with self.assertRaisesRegex(app.ValidationError, "invalid_model_schema"):
                self.preview(response, "Work on July 30, 2026")

    def test_leave_preview_builds_offline_adapter_plan(self) -> None:
        preview = self.preview(
            intent("2026-07-15", "sickness", "full_day"),
            "I was sick on July 15, 2026",
        )
        plan = contract.build_adapter_plan(preview)
        self.assertEqual(plan["state"], "previewed")
        self.assertTrue(plan["requires_confirmation"])
        self.assertEqual(plan["request_kind"], "leave")
        self.assertEqual(plan["planned_rows"][0]["date"], "2026-07-15")
        self.assertEqual(plan["planned_rows"][0]["sap_code"], "0200")
        self.assertNotIn("I was sick on July 15, 2026", json.dumps(plan))
        self.assertEqual(len(plan["plan_id"]), 64)

    def test_work_preview_builds_offline_adapter_plan(self) -> None:
        preview = self.preview(
            work_intent(
                "2026-07-30",
                favorite_code="WBS-CONTRACT-9",
                task_description="Offline contract task",
            ),
            "Work on the offline contract July 30, 2026",
        )
        plan = contract.build_adapter_plan(preview)
        self.assertEqual(plan["state"], "previewed")
        self.assertEqual(plan["request_kind"], "work")
        self.assertEqual(plan["planned_rows"][0]["favorite_code"], "WBS-CONTRACT-9")
        self.assertEqual(plan["planned_rows"][0]["task_description"], "Offline contract task")
        self.assertEqual(plan["planned_rows"][0]["billable"], True)

    def test_plan_id_is_repeatable_and_changes_with_planned_row(self) -> None:
        response = work_intent("2026-07-30")
        preview = self.preview(response, "Work on July 30, 2026")
        first = contract.build_adapter_plan(preview)
        second = contract.build_adapter_plan(json.loads(json.dumps(preview)))
        self.assertEqual(first["plan_id"], second["plan_id"])

        changed_preview = json.loads(json.dumps(preview))
        changed_preview["work_entries"][0]["task_description"] = "Changed task"
        changed = contract.build_adapter_plan(changed_preview)
        self.assertNotEqual(first["plan_id"], changed["plan_id"])

    def test_confirmation_requires_exact_unchanged_plan(self) -> None:
        plan = contract.build_adapter_plan(
            self.preview(intent("2026-07-15", "sickness", "full_day"), "I was sick on July 15, 2026")
        )
        confirmed = contract.confirm_adapter_plan(plan, plan["plan_id"])
        self.assertEqual(confirmed["state"], "awaiting_confirmation")
        self.assertTrue(confirmed["requires_confirmation"])
        self.assertEqual(
            contract.confirm_adapter_plan(plan, "0" * 64),
            {
                "schema_version": 1,
                "state": "failed",
                "requires_confirmation": False,
                "error": "plan_changed",
            },
        )

        changed = json.loads(json.dumps(plan))
        changed["planned_rows"][0]["leave_type"] = "paid_leave"
        changed["planned_rows"][0]["sap_code"] = "0600"
        failed = contract.confirm_adapter_plan(changed, plan["plan_id"])
        self.assertEqual(
            failed,
            {
                "schema_version": 1,
                "state": "failed",
                "requires_confirmation": False,
                "error": "plan_changed",
            },
        )
        self.assertEqual(
            contract.safe_log_fields(failed),
            {"state": "failed", "error": "plan_changed", "requires_confirmation": False},
        )


        unsupported = json.loads(json.dumps(plan))
        unsupported["unexpected"] = "reject"
        with self.assertRaises(contract.ContractError):
            contract.confirm_adapter_plan(unsupported, plan["plan_id"])

    def test_malformed_or_unsupported_previews_are_rejected(self) -> None:
        base = self.preview(
            intent("2026-07-15", "sickness", "full_day"),
            "I was sick on July 15, 2026",
        )
        cases = []

        clarification = json.loads(json.dumps(base))
        clarification["kind"] = "clarification"
        cases.append(clarification)

        empty = json.loads(json.dumps(base))
        empty["planned_dates"] = []
        empty["eligible_dates"] = []
        empty["eligible_date_details"] = []
        cases.append(empty)

        unknown = json.loads(json.dumps(base))
        unknown["request_kind"] = "unknown"
        cases.append(unknown)

        extra = json.loads(json.dumps(base))
        extra["unexpected"] = "reject"
        cases.append(extra)

        for malformed in cases:
            with self.assertRaises(contract.ContractError):
                contract.build_adapter_plan(malformed)

    def test_monthly_summary_is_fully_validated_before_confirmation(self) -> None:
        plan = contract.build_adapter_plan(
            self.preview(intent("2026-07-15", "sickness", "full_day"), "I was sick on July 15, 2026")
        )
        mutations = [
            ("planned_count", "bad"),
            ("full_day_count", -1),
            ("partial_day_hours", "bad"),
            ("skipped_weekends", -1),
            ("skipped_non_working_holidays", -1),
            ("skipped_existing_entries", -1),
            ("locked_status", "locked"),
            ("release_status", "released"),
            ("month", "2026-08"),
        ]
        for field, value in mutations:
            malformed = json.loads(json.dumps(plan))
            malformed["monthly_summary"][0][field] = value
            malformed = rehashed_plan(malformed)
            with self.assertRaises(contract.ContractError):
                contract.confirm_adapter_plan(malformed, malformed["plan_id"])

        malformed_skips = json.loads(json.dumps(plan))
        malformed_skips["skip_summary"]["reasons"]["weekend"] = 1
        malformed_skips = rehashed_plan(malformed_skips)
        with self.assertRaises(contract.ContractError):
            contract.confirm_adapter_plan(malformed_skips, malformed_skips["plan_id"])

    def test_failed_results_are_validated_and_safe_to_consume(self) -> None:
        plan = contract.build_adapter_plan(
            self.preview(intent("2026-07-15", "sickness", "full_day"), "I was sick on July 15, 2026")
        )
        failed = contract.confirm_adapter_plan(plan, "0" * 64)
        self.assertEqual(contract.safe_log_fields(failed)["state"], "failed")
        malformed = json.loads(json.dumps(failed))
        malformed["error"] = "raw user text"
        with self.assertRaises(contract.ContractError):
            contract.safe_log_fields(malformed)

    def test_offline_states_and_safe_log_fields_exclude_live_actions(self) -> None:
        plan = contract.build_adapter_plan(
            self.preview(
                work_intent(
                    "2026-07-30",
                    favorite_code="WBS-SECRET-7",
                    task_description="Do not log this task",
                ),
                "Work on July 30, 2026 with token=do-not-log",
            )
        )
        self.assertEqual(contract.OFFLINE_STATES, {"previewed", "awaiting_confirmation", "failed"})
        safe_fields = json.dumps(contract.safe_log_fields(plan))
        for sensitive in ("WBS-SECRET-7", "Do not log this task", "token=do-not-log", "cookie"):
            self.assertNotIn(sensitive, safe_fields)
        self.assertNotIn("plan_id", contract.safe_log_fields(plan))

        checked = json.loads(json.dumps(plan))
        checked["state"] = "checked"
        with self.assertRaises(contract.ContractError):
            contract.confirm_adapter_plan(checked, plan["plan_id"])

    def test_ollama_defaults_and_missing_model_error(self) -> None:
        extractor = app.OllamaIntentExtractor()
        self.assertEqual(extractor.model, "gemma4:12b")
        self.assertEqual(extractor.timeout, 180.0)
        override = app.OllamaIntentExtractor(model="custom:model", timeout=7.0)
        self.assertEqual(override.model, "custom:model")
        self.assertEqual(override.timeout, 7.0)

        error = app.urllib_error.HTTPError(extractor.url, 404, "model not found", {}, None)
        with mock.patch.object(app.urllib_request, "urlopen", side_effect=error) as urlopen:
            with self.assertRaises(app.OllamaError) as raised:
                extractor.extract("I was sick on July 15, 2026")
        self.assertEqual(raised.exception.code, "ollama_model_not_found")
        request_body = json.loads(urlopen.call_args.args[0].data)
        self.assertIs(request_body["think"], False)
        self.assertEqual(urlopen.call_args.kwargs["timeout"], 180.0)

    def test_http_preview_exists_but_submission_route_does_not(self) -> None:
        fake = FakeOllama(work_intent("2026-07-15"))
        server = app.make_server("127.0.0.1", 0, fake, app.JsonlLogger(self.log_path))
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        host, port = server.server_address
        try:
            connection = http.client.HTTPConnection(host, port, timeout=5)
            connection.request("GET", "/")
            page_response = connection.getresponse()
            page_body = page_response.read().decode("utf-8")
            self.assertEqual(page_response.status, 200)
            self.assertIn("leave or work request", page_body)
            connection.close()

            connection = http.client.HTTPConnection(host, port, timeout=5)
            body = json.dumps({"text": "Work on the planner on July 15, 2026"})
            connection.request("POST", "/api/preview", body, {"Content-Type": "application/json"})
            preview_response = connection.getresponse()
            preview_body = json.loads(preview_response.read())
            self.assertEqual(preview_response.status, 200)
            self.assertEqual(preview_body["request_kind"], "work")
            self.assertEqual(preview_body["work_entries"][0]["date"], "2026-07-15")
            connection.close()

            connection = http.client.HTTPConnection(host, port, timeout=5)
            connection.request("POST", "/api/submit", "{}", {"Content-Type": "application/json"})
            submission_response = connection.getresponse()
            submission_response.read()
            self.assertEqual(submission_response.status, 404)
            connection.close()
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(FeatureVerification)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        raise SystemExit(1)
    print("Dry-run harness: PASS (fake Ollama; no SAP, Edge, network, or live Ollama access)")
