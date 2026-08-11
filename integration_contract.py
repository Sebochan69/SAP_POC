from __future__ import annotations

import hashlib
import hmac
import json
import math
import re
from datetime import date
from typing import Any

DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")
MONTH_PATTERN = re.compile(r"^\d{4}-\d{2}$")
DRY_RUN_WARNING = "Dry-run only: no SAP or Edge action is available."
LOCAL_HOLIDAY_WARNING = "Holiday data is a local transcription and is not live-synchronized."
PLAN_VERSION = 1
OFFLINE_STATES = frozenset({"previewed", "awaiting_confirmation", "failed"})

_PREVIEW_KEYS = frozenset(
    {
        "dry_run",
        "kind",
        "request_kind",
        "date_range",
        "leave_type",
        "sap_code",
        "duration",
        "eligible_dates",
        "planned_dates",
        "eligible_date_details",
        "skipped_dates",
        "holiday_calendar",
        "existing_entries",
        "monthly_overview",
        "work_entries",
        "warnings",
        "clarifications",
    }
)
_PLAN_KEYS = frozenset(
    {
        "schema_version",
        "plan_id",
        "state",
        "requires_confirmation",
        "request_kind",
        "date_range",
        "planned_rows",
        "calendar_summary",
        "existing_summary",
        "monthly_summary",
        "skip_summary",
        "warnings",
    }
)
_WARNING_VALUES = frozenset({DRY_RUN_WARNING, LOCAL_HOLIDAY_WARNING})
_HOLIDAY_CATEGORIES = frozenset({"regular_holiday", "special_non_working", "special_working"})
_SKIP_REASONS = frozenset({"weekend", "holiday", "existing_entry"})
_NON_WORKING_HOLIDAY_CATEGORIES = frozenset({"regular_holiday", "special_non_working"})
_UNAVAILABLE_STATUS = "unavailable_in_dry_run"
_FAILED_ERRORS = frozenset({"plan_changed"})


class ContractError(ValueError):
    """Raised when an offline preview or adapter plan is not safe to consume."""


def _invalid(code: str = "invalid_contract") -> None:
    raise ContractError(code)


def _exact_object(value: Any, keys: tuple[str, ...], code: str = "invalid_contract") -> dict[str, Any]:
    if type(value) is not dict or set(value) != set(keys):
        _invalid(code)
    return value


def _date_value(value: Any, code: str = "invalid_date") -> str:
    if not isinstance(value, str) or DATE_PATTERN.fullmatch(value) is None:
        _invalid(code)
    try:
        date.fromisoformat(value)
    except ValueError:
        _invalid(code)
    return value


def _date_list(
    value: Any,
    *,
    allow_empty: bool,
    code: str,
    start: str | None = None,
    end: str | None = None,
) -> list[str]:
    if type(value) is not list or (not allow_empty and not value):
        _invalid(code)
    dates = [_date_value(item, code) for item in value]
    if dates != sorted(set(dates)):
        _invalid(code)
    if start is not None and end is not None:
        start_date = date.fromisoformat(start)
        end_date = date.fromisoformat(end)
        if any(not start_date <= date.fromisoformat(item) <= end_date for item in dates):
            _invalid(code)
    return dates


def _number(value: Any, code: str) -> int | float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        _invalid(code)
    if not math.isfinite(value):
        _invalid(code)
    return value


def _positive_hours(value: Any, code: str) -> int | float:
    number = _number(value, code)
    if not 0 < number <= 24:
        _invalid(code)
    return number


def _non_empty_string(value: Any, code: str) -> str:
    if not isinstance(value, str) or not value.strip():
        _invalid(code)
    return value.strip()


def _validate_duration(value: Any) -> dict[str, Any]:
    duration = _exact_object(value, ("kind", "hours"), "invalid_duration")
    kind = duration["kind"]
    hours = duration["hours"]
    if kind not in ("full_day", "hours", "unspecified"):
        _invalid("invalid_duration")
    if kind == "hours":
        hours = _positive_hours(hours, "invalid_duration")
    elif hours is not None:
        _invalid("invalid_duration")
    return {"kind": kind, "hours": hours}

def _validate_holiday(value: Any) -> dict[str, str] | None:
    if value is None:
        return None
    holiday = _exact_object(value, ("date", "name", "category"), "invalid_holiday")
    holiday_date = _date_value(holiday["date"], "invalid_holiday")
    name = _non_empty_string(holiday["name"], "invalid_holiday")
    category = holiday["category"]
    if not isinstance(category, str) or category not in _HOLIDAY_CATEGORIES:
        _invalid("invalid_holiday")
    return {"date": holiday_date, "name": name, "category": category}


def _validate_preview_detail(value: Any, expected_date: str) -> None:
    detail = _exact_object(value, ("date", "holiday"), "invalid_preview_detail")
    if _date_value(detail["date"], "invalid_preview_detail") != expected_date:
        _invalid("invalid_preview_detail")
    holiday = _validate_holiday(detail["holiday"])
    if holiday is not None and holiday["date"] != expected_date:
        _invalid("invalid_preview_detail")


def _validate_skips(value: Any, start: str, end: str) -> dict[str, Any]:
    if type(value) is not list:
        _invalid("invalid_skipped_dates")
    start_date = date.fromisoformat(start)
    end_date = date.fromisoformat(end)
    seen: set[str] = set()
    reason_counts = {reason: 0 for reason in sorted(_SKIP_REASONS)}
    holiday_counts = {category: 0 for category in sorted(_HOLIDAY_CATEGORIES)}
    monthly_counts: dict[str, dict[str, dict[str, int]]] = {}
    for item in value:
        if type(item) is not dict or "date" not in item or "reason" not in item:
            _invalid("invalid_skipped_dates")
        skipped_date = _date_value(item["date"], "invalid_skipped_dates")
        parsed_date = date.fromisoformat(skipped_date)
        if not start_date <= parsed_date <= end_date or skipped_date in seen:
            _invalid("invalid_skipped_dates")
        seen.add(skipped_date)
        reason = item["reason"]
        if not isinstance(reason, str) or reason not in _SKIP_REASONS:
            _invalid("invalid_skipped_dates")
        reason_counts[reason] += 1
        month_counts = monthly_counts.setdefault(
            skipped_date[:7],
            {
                "reasons": {key: 0 for key in sorted(_SKIP_REASONS)},
                "holiday_categories": {key: 0 for key in sorted(_HOLIDAY_CATEGORIES)},
            },
        )
        month_counts["reasons"][reason] += 1
        if reason in ("weekend", "holiday"):
            if set(item) != {"date", "reason", "holiday"}:
                _invalid("invalid_skipped_dates")
            holiday = _validate_holiday(item["holiday"])
            if reason == "holiday" and (
                holiday is None or holiday["category"] not in _NON_WORKING_HOLIDAY_CATEGORIES
            ):
                _invalid("invalid_skipped_dates")
            if holiday is not None:
                if holiday["date"] != skipped_date:
                    _invalid("invalid_skipped_dates")
                holiday_counts[holiday["category"]] += 1
                month_counts["holiday_categories"][holiday["category"]] += 1
        else:
            if set(item) != {"date", "reason", "existing_entry"}:
                _invalid("invalid_skipped_dates")
            reference = _exact_object(
                item["existing_entry"],
                ("snapshot_name", "source"),
                "invalid_skipped_dates",
            )
            _non_empty_string(reference["snapshot_name"], "invalid_skipped_dates")
            source = _exact_object(reference["source"], ("kind", "note"), "invalid_skipped_dates")
            if source["kind"] != "local_fixture":
                _invalid("invalid_skipped_dates")
            _non_empty_string(source["note"], "invalid_skipped_dates")
    return {
        "reasons": reason_counts,
        "holiday_categories": holiday_counts,
        "monthly": monthly_counts,
    }


def _expected_months(start: str, end: str) -> list[str]:
    current = date.fromisoformat(start).replace(day=1)
    end_month = date.fromisoformat(end).replace(day=1)
    months: list[str] = []
    while current <= end_month:
        months.append(current.strftime("%Y-%m"))
        if current.month == 12:
            current = current.replace(year=current.year + 1, month=1)
        else:
            current = current.replace(month=current.month + 1)
    return months


def _nonnegative_count(value: Any, code: str) -> int:
    if type(value) is not int or value < 0:
        _invalid(code)
    return value


def _validate_count_map(value: Any, keys: frozenset[str], code: str) -> dict[str, int]:
    if type(value) is not dict or set(value) != set(keys):
        _invalid(code)
    return {key: _nonnegative_count(value[key], code) for key in sorted(keys)}


def _validate_skip_summary(value: Any, start: str, end: str, code: str) -> dict[str, Any]:
    summary = _exact_object(value, ("reasons", "holiday_categories", "monthly"), code)
    reasons = _validate_count_map(summary["reasons"], _SKIP_REASONS, code)
    holiday_categories = _validate_count_map(summary["holiday_categories"], _HOLIDAY_CATEGORIES, code)
    monthly = summary["monthly"]
    if type(monthly) is not dict:
        _invalid(code)
    expected_months = set(_expected_months(start, end))
    normalized_monthly: dict[str, dict[str, dict[str, int]]] = {}
    for month, counts in monthly.items():
        if not isinstance(month, str) or MONTH_PATTERN.fullmatch(month) is None or month not in expected_months:
            _invalid(code)
        counts = _exact_object(counts, ("reasons", "holiday_categories"), code)
        normalized_monthly[month] = {
            "reasons": _validate_count_map(counts["reasons"], _SKIP_REASONS, code),
            "holiday_categories": _validate_count_map(
                counts["holiday_categories"],
                _HOLIDAY_CATEGORIES,
                code,
            ),
        }
    for reason in _SKIP_REASONS:
        if sum(item["reasons"][reason] for item in normalized_monthly.values()) != reasons[reason]:
            _invalid(code)
    for category in _HOLIDAY_CATEGORIES:
        if (
            sum(item["holiday_categories"][category] for item in normalized_monthly.values())
            != holiday_categories[category]
        ):
            _invalid(code)
    return {
        "reasons": reasons,
        "holiday_categories": holiday_categories,
        "monthly": normalized_monthly,
    }


def _validate_monthly_summary(
    value: Any,
    start: str,
    end: str,
    planned_rows: list[dict[str, Any]],
    request_kind: str,
    skip_summary: dict[str, Any],
    code: str,
) -> None:
    if type(value) is not list or not value:
        _invalid(code)
    expected_months = _expected_months(start, end)
    if len(value) != len(expected_months):
        _invalid(code)
    row_dates: list[str] = []
    for row in planned_rows:
        if type(row) is not dict or "date" not in row:
            _invalid(code)
        row_date = _date_value(row["date"], code)
        if not date.fromisoformat(start) <= date.fromisoformat(row_date) <= date.fromisoformat(end):
            _invalid(code)
        row_dates.append(row_date)
    if row_dates != sorted(set(row_dates)):
        _invalid(code)
    planned_by_month = {
        month: [row for row in planned_rows if row["date"][:7] == month]
        for month in expected_months
    }
    zero_month = {
        "reasons": {key: 0 for key in sorted(_SKIP_REASONS)},
        "holiday_categories": {key: 0 for key in sorted(_HOLIDAY_CATEGORIES)},
    }
    for month, item in zip(expected_months, value):
        summary = _exact_object(
            item,
            (
                "month",
                "planned_count",
                "full_day_count",
                "partial_day_hours",
                "skipped_weekends",
                "skipped_non_working_holidays",
                "skipped_existing_entries",
                "locked_status",
                "release_status",
            ),
            code,
        )
        if not isinstance(summary["month"], str) or summary["month"] != month:
            _invalid(code)
        planned_count = _nonnegative_count(summary["planned_count"], code)
        month_rows = planned_by_month[month]
        if planned_count != len(month_rows):
            _invalid(code)
        full_day_count = _nonnegative_count(summary["full_day_count"], code)
        partial_day_hours = _number(summary["partial_day_hours"], code)
        if partial_day_hours < 0:
            _invalid(code)
        for field in (
            "skipped_weekends",
            "skipped_non_working_holidays",
            "skipped_existing_entries",
        ):
            _nonnegative_count(summary[field], code)
        if summary["locked_status"] != _UNAVAILABLE_STATUS:
            _invalid(code)
        if summary["release_status"] != _UNAVAILABLE_STATUS:
            _invalid(code)

        expected_full_days = 0
        expected_partial_hours: int | float = 0
        for row in month_rows:
            if request_kind == "leave":
                duration = _validate_duration(row["duration"])
                if duration["kind"] == "unspecified":
                    _invalid(code)
                if duration["kind"] == "full_day":
                    expected_full_days += 1
                else:
                    expected_partial_hours += duration["hours"]
            else:
                expected_partial_hours += _positive_hours(row["hours_per_day"], code)
        if full_day_count != expected_full_days or partial_day_hours != expected_partial_hours:
            _invalid(code)

        month_skips = skip_summary["monthly"].get(month, zero_month)
        if summary["skipped_weekends"] != month_skips["reasons"]["weekend"]:
            _invalid(code)
        if summary["skipped_existing_entries"] != month_skips["reasons"]["existing_entry"]:
            _invalid(code)
        expected_non_working = sum(
            month_skips["holiday_categories"][category]
            for category in _NON_WORKING_HOLIDAY_CATEGORIES
        )
        if summary["skipped_non_working_holidays"] != expected_non_working:
            _invalid(code)


def _validate_monthly_overview(
    value: Any,
    start: str,
    end: str,
    planned_rows: list[dict[str, Any]],
    request_kind: str,
    skip_summary: dict[str, Any],
) -> list[dict[str, Any]]:
    if type(value) is not list or not value:
        _invalid("invalid_monthly_overview")
    expected_months = _expected_months(start, end)
    if len(value) != len(expected_months):
        _invalid("invalid_monthly_overview")
    planned_dates = [row["date"] for row in planned_rows]
    summaries: list[dict[str, Any]] = []
    for month, item in zip(expected_months, value):
        overview = _exact_object(
            item,
            (
                "month",
                "eligible_dates",
                "planned_dates",
                "full_day_count",
                "partial_day_hours",
                "skipped_weekends",
                "skipped_non_working_holidays",
                "skipped_existing_entries",
                "locked_status",
                "release_status",
                "warnings",
            ),
            "invalid_monthly_overview",
        )
        if not isinstance(overview["month"], str) or overview["month"] != month:
            _invalid("invalid_monthly_overview")
        month_planned = _date_list(
            overview["planned_dates"],
            allow_empty=True,
            code="invalid_monthly_overview",
            start=start,
            end=end,
        )
        month_eligible = _date_list(
            overview["eligible_dates"],
            allow_empty=True,
            code="invalid_monthly_overview",
            start=start,
            end=end,
        )
        expected_planned = [planned_date for planned_date in planned_dates if planned_date[:7] == month]
        if month_eligible != expected_planned or month_planned != expected_planned:
            _invalid("invalid_monthly_overview")
        if overview["warnings"] != [DRY_RUN_WARNING]:
            _invalid("invalid_monthly_overview")
        summaries.append(
            {
                "month": month,
                "planned_count": len(month_planned),
                "full_day_count": overview["full_day_count"],
                "partial_day_hours": overview["partial_day_hours"],
                "skipped_weekends": overview["skipped_weekends"],
                "skipped_non_working_holidays": overview["skipped_non_working_holidays"],
                "skipped_existing_entries": overview["skipped_existing_entries"],
                "locked_status": overview["locked_status"],
                "release_status": overview["release_status"],
            }
        )
    _validate_monthly_summary(
        summaries,
        start,
        end,
        planned_rows,
        request_kind,
        skip_summary,
        "invalid_monthly_overview",
    )
    return summaries


def _validate_metadata(preview: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    calendar = _exact_object(preview["holiday_calendar"], ("name", "year", "source"), "invalid_calendar")
    if not isinstance(calendar["name"], str) or not calendar["name"].strip() or type(calendar["year"]) is not int:
        _invalid("invalid_calendar")
    source = _exact_object(
        calendar["source"],
        ("title", "url", "revision_date", "live_validated", "note"),
        "invalid_calendar",
    )
    for field in ("title", "url", "revision_date", "note"):
        _non_empty_string(source[field], "invalid_calendar")
    if type(source["live_validated"]) is not bool:
        _invalid("invalid_calendar")
    calendar_summary = {"year": calendar["year"], "live_validated": source["live_validated"]}

    existing = _exact_object(
        preview["existing_entries"],
        ("configured", "name", "year", "source", "entry_count"),
        "invalid_existing_entries",
    )
    if type(existing["configured"]) is not bool:
        _invalid("invalid_existing_entries")
    if existing["name"] is not None:
        _non_empty_string(existing["name"], "invalid_existing_entries")
    if existing["year"] is not None and type(existing["year"]) is not int:
        _invalid("invalid_existing_entries")
    if type(existing["entry_count"]) is not int or existing["entry_count"] < 0:
        _invalid("invalid_existing_entries")
    existing_source = _exact_object(existing["source"], ("kind", "note"), "invalid_existing_entries")
    if existing_source["kind"] not in ("none", "local_fixture"):
        _invalid("invalid_existing_entries")
    _non_empty_string(existing_source["note"], "invalid_existing_entries")
    if existing["configured"] != (existing_source["kind"] == "local_fixture"):
        _invalid("invalid_existing_entries")
    existing_summary = {
        "configured": existing["configured"],
        "year": existing["year"],
        "entry_count": existing["entry_count"],
        "source_kind": existing_source["kind"],
    }
    return calendar_summary, existing_summary


def _validate_warnings(value: Any, code: str) -> list[str]:
    if type(value) is not list or any(not isinstance(warning, str) for warning in value):
        _invalid(code)
    if len(value) != len(set(value)) or any(warning not in _WARNING_VALUES for warning in value):
        _invalid(code)
    if DRY_RUN_WARNING not in value:
        _invalid(code)
    return [warning for warning in (DRY_RUN_WARNING, LOCAL_HOLIDAY_WARNING) if warning in value]

def _validate_preview(preview: Any) -> dict[str, Any]:
    if type(preview) is not dict or set(preview) != _PREVIEW_KEYS:
        _invalid("invalid_preview")
    if preview["dry_run"] is not True or preview["kind"] != "preview":
        _invalid("invalid_preview")
    if preview["request_kind"] not in ("leave", "work"):
        _invalid("invalid_request_kind")
    if type(preview["clarifications"]) is not list or preview["clarifications"]:
        _invalid("unresolved_clarification")
    if any(not isinstance(item, str) or not item.strip() for item in preview["clarifications"]):
        _invalid("invalid_preview")
    safe_warnings = _validate_warnings(preview["warnings"], "invalid_preview")

    date_range = _exact_object(preview["date_range"], ("start", "end"), "invalid_date_range")
    start = _date_value(date_range["start"], "invalid_date_range")
    end = _date_value(date_range["end"], "invalid_date_range")
    if start > end:
        _invalid("invalid_date_range")
    planned_dates = _date_list(
        preview["planned_dates"],
        allow_empty=False,
        code="empty_plan",
        start=start,
        end=end,
    )
    eligible_dates = _date_list(
        preview["eligible_dates"],
        allow_empty=False,
        code="invalid_preview",
        start=start,
        end=end,
    )
    if eligible_dates != planned_dates:
        _invalid("invalid_preview")
    details = preview["eligible_date_details"]
    if type(details) is not list or len(details) != len(planned_dates):
        _invalid("invalid_preview_detail")
    for detail, planned_date in zip(details, planned_dates):
        _validate_preview_detail(detail, planned_date)

    request_kind = preview["request_kind"]
    leave_type = preview["leave_type"]
    sap_code = preview["sap_code"]
    duration = _validate_duration(preview["duration"])
    if request_kind == "leave":
        if (
            leave_type not in ("sickness", "paid_leave")
            or sap_code not in ("0200", "0600")
            or duration["kind"] == "unspecified"
        ):
            _invalid("invalid_leave")
        if sap_code != {"sickness": "0200", "paid_leave": "0600"}[leave_type]:
            _invalid("invalid_leave")
    else:
        if leave_type != "unknown" or sap_code is not None or duration != {"kind": "unspecified", "hours": None}:
            _invalid("invalid_work")

    work_entries = preview["work_entries"]
    rows: list[dict[str, Any]] = []
    if request_kind == "leave":
        if work_entries != []:
            _invalid("invalid_leave")
        rows = [
            {
                "request_kind": "leave",
                "date": planned_date,
                "leave_type": leave_type,
                "sap_code": sap_code,
                "duration": dict(duration),
            }
            for planned_date in planned_dates
        ]
    else:
        if type(work_entries) is not list or not work_entries:
            _invalid("empty_plan")
        row_dates: list[str] = []
        for entry in work_entries:
            work_entry = _exact_object(
                entry,
                ("date", "favorite_code", "hours_per_day", "billable", "task_description"),
                "invalid_work_entry",
            )
            entry_date = _date_value(work_entry["date"], "invalid_work_entry")
            if not start <= entry_date <= end:
                _invalid("invalid_work_entry")
            favorite_code = _non_empty_string(work_entry["favorite_code"], "invalid_work_entry")
            hours_per_day = _positive_hours(work_entry["hours_per_day"], "invalid_work_entry")
            billable = work_entry["billable"]
            if type(billable) is not bool:
                _invalid("invalid_work_entry")
            task_description = _non_empty_string(work_entry["task_description"], "invalid_work_entry")
            row_dates.append(entry_date)
            rows.append(
                {
                    "request_kind": "work",
                    "date": entry_date,
                    "favorite_code": favorite_code,
                    "hours_per_day": hours_per_day,
                    "billable": billable,
                    "task_description": task_description,
                }
            )
        if row_dates != planned_dates:
            _invalid("invalid_work_entry")

    skip_summary = _validate_skips(preview["skipped_dates"], start, end)
    calendar_summary, existing_summary = _validate_metadata(preview)
    monthly_summary = _validate_monthly_overview(
        preview["monthly_overview"],
        start,
        end,
        rows,
        request_kind,
        skip_summary,
    )
    return {
        "request_kind": request_kind,
        "date_range": {"start": start, "end": end},
        "planned_rows": rows,
        "calendar_summary": calendar_summary,
        "existing_summary": existing_summary,
        "monthly_summary": monthly_summary,
        "skip_summary": skip_summary,
        "warnings": safe_warnings,
    }


def _canonical_payload(data: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": PLAN_VERSION,
        "request_kind": data["request_kind"],
        "date_range": data["date_range"],
        "planned_rows": data["planned_rows"],
        "calendar_summary": data["calendar_summary"],
        "existing_summary": data["existing_summary"],
        "monthly_summary": data["monthly_summary"],
        "skip_summary": data["skip_summary"],
        "warnings": data["warnings"],
    }


def _plan_id(data: dict[str, Any]) -> str:
    canonical = _canonical_payload(data)
    canonical.update({"state": "previewed", "requires_confirmation": True})
    encoded = json.dumps(
        canonical,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def build_adapter_plan(preview: Any) -> dict[str, Any]:
    """Build a deterministic, offline-only adapter plan from an app preview."""
    data = _validate_preview(preview)
    plan = _canonical_payload(data)
    plan.update(
        {
            "plan_id": _plan_id(data),
            "state": "previewed",
            "requires_confirmation": True,
        }
    )
    return plan


def _validate_plan(plan: Any, *, allowed_states: frozenset[str]) -> dict[str, Any]:
    if type(plan) is not dict or set(plan) != _PLAN_KEYS:
        _invalid("invalid_plan")
    if (
        plan["schema_version"] != PLAN_VERSION
        or not isinstance(plan["state"], str)
        or plan["state"] not in allowed_states
    ):
        _invalid("invalid_plan")
    if type(plan["plan_id"]) is not str or re.fullmatch(r"[0-9a-f]{64}", plan["plan_id"]) is None:
        _invalid("invalid_plan")
    if plan["requires_confirmation"] is not True:
        _invalid("invalid_plan")
    data = {
        "request_kind": plan["request_kind"],
        "date_range": plan["date_range"],
        "planned_rows": plan["planned_rows"],
        "calendar_summary": plan["calendar_summary"],
        "existing_summary": plan["existing_summary"],
        "monthly_summary": plan["monthly_summary"],
        "skip_summary": plan["skip_summary"],
        "warnings": plan["warnings"],
    }
    if data["request_kind"] not in ("leave", "work"):
        _invalid("invalid_plan")
    date_range = _exact_object(data["date_range"], ("start", "end"), "invalid_plan")
    start = _date_value(date_range["start"], "invalid_plan")
    end = _date_value(date_range["end"], "invalid_plan")
    if start > end:
        _invalid("invalid_plan")
    planned_rows = data["planned_rows"]
    if type(planned_rows) is not list or not planned_rows:
        _invalid("invalid_plan")
    previous_date: str | None = None
    for row in planned_rows:
        if type(row) is not dict or "request_kind" not in row or "date" not in row:
            _invalid("invalid_plan")
        row_date = _date_value(row["date"], "invalid_plan")
        if not start <= row_date <= end or (previous_date is not None and row_date <= previous_date):
            _invalid("invalid_plan")
        previous_date = row_date
        if row["request_kind"] != data["request_kind"]:
            _invalid("invalid_plan")
        if data["request_kind"] == "leave":
            if set(row) != {"request_kind", "date", "leave_type", "sap_code", "duration"}:
                _invalid("invalid_plan")
            if row["leave_type"] not in ("sickness", "paid_leave"):
                _invalid("invalid_plan")
            if row["sap_code"] != {"sickness": "0200", "paid_leave": "0600"}[row["leave_type"]]:
                _invalid("invalid_plan")
            duration = _validate_duration(row["duration"])
            if duration["kind"] == "unspecified":
                _invalid("invalid_plan")
        else:
            if set(row) != {
                "request_kind",
                "date",
                "favorite_code",
                "hours_per_day",
                "billable",
                "task_description",
            }:
                _invalid("invalid_plan")
            _non_empty_string(row["favorite_code"], "invalid_plan")
            _positive_hours(row["hours_per_day"], "invalid_plan")
            if type(row["billable"]) is not bool:
                _invalid("invalid_plan")
            _non_empty_string(row["task_description"], "invalid_plan")

    calendar = _exact_object(data["calendar_summary"], ("year", "live_validated"), "invalid_plan")
    if type(calendar["year"]) is not int or type(calendar["live_validated"]) is not bool:
        _invalid("invalid_plan")
    existing = _exact_object(
        data["existing_summary"],
        ("configured", "year", "entry_count", "source_kind"),
        "invalid_plan",
    )
    if type(existing["configured"]) is not bool:
        _invalid("invalid_plan")
    if existing["year"] is not None and type(existing["year"]) is not int:
        _invalid("invalid_plan")
    _nonnegative_count(existing["entry_count"], "invalid_plan")
    if existing["source_kind"] not in ("none", "local_fixture"):
        _invalid("invalid_plan")

    skip_summary = _validate_skip_summary(data["skip_summary"], start, end, "invalid_plan")
    _validate_warnings(data["warnings"], "invalid_plan")
    _validate_monthly_summary(
        data["monthly_summary"],
        start,
        end,
        planned_rows,
        data["request_kind"],
        skip_summary,
        "invalid_plan",
    )
    return data


def _validate_failed(value: Any) -> dict[str, Any]:
    result = _exact_object(
        value,
        ("schema_version", "state", "requires_confirmation", "error"),
        "invalid_failed_result",
    )
    if (
        result["schema_version"] != PLAN_VERSION
        or result["state"] != "failed"
        or result["requires_confirmation"] is not False
        or not isinstance(result["error"], str)
        or result["error"] not in _FAILED_ERRORS
    ):
        _invalid("invalid_failed_result")
    return result


def _failed(reason: str) -> dict[str, Any]:
    result = {
        "schema_version": PLAN_VERSION,
        "state": "failed",
        "requires_confirmation": False,
        "error": reason,
    }
    _validate_failed(result)
    return result


def confirm_adapter_plan(plan: Any, expected_plan_id: Any) -> dict[str, Any]:
    """Return an awaiting-confirmation copy only when the immutable hash matches."""
    data = _validate_plan(plan, allowed_states=frozenset({"previewed"}))
    if type(expected_plan_id) is not str:
        _invalid("invalid_plan_id")
    actual_plan_id = _plan_id(data)
    if (
        not hmac.compare_digest(actual_plan_id, plan["plan_id"])
        or not hmac.compare_digest(actual_plan_id, expected_plan_id)
    ):
        return _failed("plan_changed")
    confirmed = dict(plan)
    confirmed["state"] = "awaiting_confirmation"
    return confirmed


def safe_log_fields(plan: Any) -> dict[str, Any]:
    """Return only counts/categories suitable for structured logs."""
    if type(plan) is dict and plan.get("state") == "failed":
        failed = _validate_failed(plan)
        return {
            "state": failed["state"],
            "error": failed["error"],
            "requires_confirmation": failed["requires_confirmation"],
        }
    data = _validate_plan(plan, allowed_states=frozenset({"previewed", "awaiting_confirmation"}))
    return {
        "state": plan["state"],
        "request_kind": data["request_kind"],
        "planned_count": len(data["planned_rows"]),
        "monthly_count": len(data["monthly_summary"]),
        "skip_reasons": dict(data["skip_summary"]["reasons"]),
        "requires_confirmation": plan["requires_confirmation"],
    }
