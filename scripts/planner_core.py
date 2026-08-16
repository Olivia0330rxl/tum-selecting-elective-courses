#!/usr/bin/env python3
"""Deterministic core helpers for the TUM elective planner."""

from __future__ import annotations

import argparse
import copy
import datetime as dt
import difflib
import json
import re
import sys
import unicodedata
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable


SCHEMA_VERSION = "1.0"
VALID_STATUSES = {"candidate", "planned", "enrolled"}
VALID_SOURCE_KINDS = {
    "my_studies",  # schema 1.0 compatibility; the default workflow is public-only
    "module_outline",
    "public_curriculum",
    "public_degree_programme",
    "public_course",
    "manual",
}
TIME_RE = re.compile(r"^(?:[01]\d|2[0-3]):[0-5]\d$")
PROHIBITED_KEY_RE = re.compile(
    r"(?:password|passwd|passphrase|credential|secret|token|cookie|session[_-]?id|"
    r"otp|mfa|student[_-]?id|matriculation|matrikel|email|e-mail|grade|exam[_-]?result|"
    r"first[_-]?name|last[_-]?name|full[_-]?name|account[_-]?id|raw[_-]?(?:html|dom|page))",
    re.IGNORECASE,
)


class PlannerValidationError(ValueError):
    """Raised when normalized planner data violates a required invariant."""


@dataclass(frozen=True)
class Term:
    kind: str
    start_year: int

    @property
    def end_year(self) -> int:
        return self.start_year + (1 if self.kind == "winter" else 0)

    @property
    def code(self) -> str:
        if self.kind == "summer":
            return f"SS-{self.start_year}"
        return f"WS-{self.start_year}-{str(self.start_year + 1)[-2:]}"

    @property
    def label_en(self) -> str:
        if self.kind == "summer":
            return f"Summer Semester {self.start_year}"
        return f"Winter Semester {self.start_year}/{str(self.start_year + 1)[-2:]}"

    @property
    def label_de(self) -> str:
        if self.kind == "summer":
            return f"Sommersemester {self.start_year}"
        return f"Wintersemester {self.start_year}/{str(self.start_year + 1)[-2:]}"


def current_term(on_date: dt.date) -> Term:
    """Return the official TUM semester containing a calendar date.

    Summer semester is April 1 through September 30. Winter semester is
    October 1 through March 31 and is named by the year in which it starts.
    """

    if 4 <= on_date.month <= 9:
        return Term("summer", on_date.year)
    if on_date.month >= 10:
        return Term("winter", on_date.year)
    return Term("winter", on_date.year - 1)


def next_term(term: Term) -> Term:
    if term.kind == "summer":
        return Term("winter", term.start_year)
    if term.kind == "winter":
        return Term("summer", term.start_year + 1)
    raise ValueError(f"Unsupported term kind: {term.kind}")


def planning_terms(on_date: dt.date) -> dict[str, Any]:
    current = current_term(on_date)
    target = next_term(current)
    return {
        "current": asdict(current) | {"code": current.code, "label": current.label_en},
        "target": asdict(target) | {"code": target.code, "label": target.label_en},
        "derived_from": on_date.isoformat(),
        "method": "next_official_tum_semester",
    }


def normalize_program_name(value: str) -> str:
    value = unicodedata.normalize("NFKD", value).casefold()
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    value = value.replace("&", " and ")
    value = re.sub(r"\b(?:m\.?sc\.?|b\.?sc\.?|master(?:'s)?|bachelor(?:'s)?)\b", " ", value)
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return " ".join(value.split())


def _program_label(item: Any) -> str:
    if isinstance(item, str):
        return item
    if isinstance(item, dict) and isinstance(item.get("name"), str):
        return item["name"]
    raise ValueError("Program candidates must be strings or objects with a string 'name'")


def match_program(
    query: str,
    programs: Iterable[Any],
    threshold: float = 0.62,
    ambiguity_margin: float = 0.08,
) -> dict[str, Any]:
    """Return exact, suggest, ambiguous, or not_found with at most 3 candidates."""

    query_norm = normalize_program_name(query)
    if not query_norm:
        return {"status": "not_found", "candidates": []}

    scored: list[dict[str, Any]] = []
    for item in programs:
        label = _program_label(item)
        normalized = normalize_program_name(label)
        if not normalized:
            continue
        if normalized == query_norm:
            return {"status": "exact", "candidate": item, "score": 1.0, "candidates": [item]}
        sequence = difflib.SequenceMatcher(None, query_norm, normalized).ratio()
        query_tokens, candidate_tokens = set(query_norm.split()), set(normalized.split())
        overlap = len(query_tokens & candidate_tokens) / max(1, len(query_tokens | candidate_tokens))
        containment = 1.0 if query_norm in normalized or normalized in query_norm else 0.0
        score = max(sequence, overlap * 0.9 + containment * 0.1)
        scored.append({"candidate": item, "score": round(score, 4)})

    scored.sort(key=lambda row: (-row["score"], _program_label(row["candidate"]).casefold()))
    viable = [row for row in scored if row["score"] >= threshold][:3]
    if not viable:
        return {"status": "not_found", "candidates": []}
    if len(viable) == 1 or viable[0]["score"] - viable[1]["score"] >= ambiguity_margin:
        return {
            "status": "suggest",
            "candidate": viable[0]["candidate"],
            "score": viable[0]["score"],
            "candidates": [viable[0]["candidate"]],
        }
    return {
        "status": "ambiguous",
        "candidates": [row["candidate"] for row in viable],
        "scores": [row["score"] for row in viable],
    }


def sanitize_personal_data(value: Any) -> Any:
    """Recursively remove keys that must never enter the planner artifact."""

    if isinstance(value, dict):
        return {
            key: sanitize_personal_data(child)
            for key, child in value.items()
            if not PROHIBITED_KEY_RE.search(str(key))
        }
    if isinstance(value, list):
        return [sanitize_personal_data(child) for child in value]
    return copy.deepcopy(value)


def paginate_results(items: Iterable[Any], page_size: int = 100) -> list[list[Any]]:
    """Split visible results into bounded pages without issuing network requests."""

    if not isinstance(page_size, int) or not 1 <= page_size <= 100:
        raise ValueError("page_size must be between 1 and 100")
    materialized = list(items)
    return [materialized[index : index + page_size] for index in range(0, len(materialized), page_size)]


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise PlannerValidationError(message)


def _minutes(value: str) -> int:
    hours, minutes = map(int, value.split(":"))
    return hours * 60 + minutes


def validate_plan(data: dict[str, Any]) -> None:
    """Validate privacy-safe normalized data and cross-field invariants."""

    _require(isinstance(data, dict), "Plan must be a JSON object")
    _require(data.get("schema_version") == SCHEMA_VERSION, "schema_version must be '1.0'")
    _require(not any(PROHIBITED_KEY_RE.search(str(key)) for key in _walk_keys(data)), "Plan contains prohibited personal-data keys")

    planning = data.get("planning_term")
    _require(isinstance(planning, dict), "planning_term is required")
    target = planning.get("target")
    _require(isinstance(target, dict), "planning_term.target is required")
    target_code = target.get("code")
    target_id = target.get("term_id")
    _require(isinstance(target_code, str) and bool(target_code), "planning_term.target.code is required")
    _require(planning.get("method") in {"next_official_tum_semester", "user_override"}, "Invalid planning_term.method")

    profile = data.get("program")
    _require(isinstance(profile, dict) and isinstance(profile.get("name"), str), "program.name is required")
    _validate_source(profile.get("source"), "program.source")

    categories = data.get("categories")
    _require(isinstance(categories, list), "categories must be an array")
    category_ids: set[str] = set()
    for index, category in enumerate(categories):
        _require(isinstance(category, dict), f"categories[{index}] must be an object")
        category_id = category.get("id")
        _require(isinstance(category_id, str) and category_id, f"categories[{index}].id is required")
        _require(category_id not in category_ids, f"Duplicate category id: {category_id}")
        category_ids.add(category_id)
        _require(isinstance(category.get("label"), str) and category["label"], f"categories[{index}].label is required")
        for field in ("min_ects", "max_ects"):
            amount = category.get(field)
            _require(amount is None or (isinstance(amount, (int, float)) and amount >= 0), f"Invalid {field} for {category_id}")
        if category.get("min_ects") is not None and category.get("max_ects") is not None:
            _require(category["min_ects"] <= category["max_ects"], f"min_ects exceeds max_ects for {category_id}")
        _validate_source(category.get("source"), f"categories[{index}].source")

    tracks = data.get("tracks", [])
    _require(isinstance(tracks, list), "tracks must be an array")
    track_ids: set[str] = set()
    for index, track in enumerate(tracks):
        prefix = f"tracks[{index}]"
        _require(isinstance(track, dict), f"{prefix} must be an object")
        track_id = track.get("id")
        _require(isinstance(track_id, str) and track_id, f"{prefix}.id is required")
        _require(track_id not in track_ids, f"Duplicate track id: {track_id}")
        track_ids.add(track_id)
        _require(isinstance(track.get("label"), str) and track["label"], f"{prefix}.label is required")
        _validate_source(track.get("source"), f"{prefix}.source")

    aggregate_requirements = data.get("aggregate_requirements", [])
    _require(isinstance(aggregate_requirements, list), "aggregate_requirements must be an array")
    aggregate_ids: set[str] = set()
    for index, requirement in enumerate(aggregate_requirements):
        prefix = f"aggregate_requirements[{index}]"
        _require(isinstance(requirement, dict), f"{prefix} must be an object")
        requirement_id = requirement.get("id")
        _require(isinstance(requirement_id, str) and requirement_id, f"{prefix}.id is required")
        _require(requirement_id not in aggregate_ids, f"Duplicate aggregate requirement id: {requirement_id}")
        aggregate_ids.add(requirement_id)
        _require(isinstance(requirement.get("label"), str) and requirement["label"], f"{prefix}.label is required")
        included = requirement.get("category_ids")
        _require(isinstance(included, list) and included, f"{prefix}.category_ids must be a non-empty array")
        _require(len(included) == len(set(included)), f"{prefix}.category_ids contains duplicates")
        _require(all(item in category_ids for item in included), f"{prefix}.category_ids contains an unknown category")
        for field in ("min_ects", "max_ects"):
            amount = requirement.get(field)
            _require(amount is None or (isinstance(amount, (int, float)) and amount >= 0), f"Invalid {field} for {requirement_id}")
        if requirement.get("min_ects") is not None and requirement.get("max_ects") is not None:
            _require(requirement["min_ects"] <= requirement["max_ects"], f"min_ects exceeds max_ects for {requirement_id}")
        _validate_source(requirement.get("source"), f"{prefix}.source")

    courses = data.get("courses")
    _require(isinstance(courses, list), "courses must be an array")
    course_ids: set[str] = set()
    for index, course in enumerate(courses):
        prefix = f"courses[{index}]"
        _require(isinstance(course, dict), f"{prefix} must be an object")
        course_id = course.get("id")
        _require(isinstance(course_id, str) and course_id, f"{prefix}.id is required")
        _require(course_id not in course_ids, f"Duplicate course id: {course_id}")
        course_ids.add(course_id)
        _require(isinstance(course.get("title"), str) and course["title"], f"{prefix}.title is required")
        _require(course.get("status") in VALID_STATUSES, f"Invalid status for {course_id}")
        _require(course.get("term") == target_code, f"Course {course_id} does not belong to target term {target_code}")
        if target_id is not None and course.get("term_id") is not None:
            _require(str(course["term_id"]) == str(target_id), f"Course {course_id} has a different target term ID")
        category_id = course.get("category_id")
        _require(category_id is None or category_id in category_ids, f"Unknown category for {course_id}: {category_id}")
        course_track_ids = course.get("track_ids", [])
        _require(isinstance(course_track_ids, list), f"{prefix}.track_ids must be an array")
        _require(len(course_track_ids) == len(set(course_track_ids)), f"{prefix}.track_ids contains duplicates")
        _require(all(item in track_ids for item in course_track_ids), f"{prefix}.track_ids contains an unknown track")
        _require(course.get("schedule_status", "unverified") in {"published", "unpublished", "unverified"}, f"Invalid schedule_status for {course_id}")
        registration = course.get("registration", {"status": "unknown"})
        _require(isinstance(registration, dict), f"{prefix}.registration must be an object")
        _require(registration.get("status") in {"open", "upcoming", "closed", "none", "unknown"}, f"Invalid registration status for {course_id}")
        ects = course.get("ects")
        _require(ects is None or (isinstance(ects, (int, float)) and ects >= 0), f"Invalid ECTS for {course_id}")
        _validate_source(course.get("source"), f"{prefix}.source")
        evidence = course.get("evidence", [])
        _require(isinstance(evidence, list), f"{prefix}.evidence must be an array")
        for evidence_index, source in enumerate(evidence):
            _validate_source(source, f"{prefix}.evidence[{evidence_index}]")

        groups = course.get("session_groups", [])
        _require(isinstance(groups, list), f"{prefix}.session_groups must be an array")
        group_ids: set[str] = set()
        for group_index, group in enumerate(groups):
            group_prefix = f"{prefix}.session_groups[{group_index}]"
            _require(isinstance(group, dict), f"{group_prefix} must be an object")
            group_id = group.get("id")
            _require(isinstance(group_id, str) and group_id, f"{group_prefix}.id is required")
            _require(group_id not in group_ids, f"Duplicate session group {group_id} for {course_id}")
            group_ids.add(group_id)
            meetings = group.get("meetings", [])
            _require(isinstance(meetings, list), f"{group_prefix}.meetings must be an array")
            for meeting_index, meeting in enumerate(meetings):
                meeting_prefix = f"{group_prefix}.meetings[{meeting_index}]"
                _require(isinstance(meeting, dict), f"{meeting_prefix} must be an object")
                _require(isinstance(meeting.get("day"), int) and 1 <= meeting["day"] <= 7, f"Invalid day at {meeting_prefix}")
                start, end = meeting.get("start"), meeting.get("end")
                _require(isinstance(start, str) and TIME_RE.match(start) is not None, f"Invalid start at {meeting_prefix}")
                _require(isinstance(end, str) and TIME_RE.match(end) is not None, f"Invalid end at {meeting_prefix}")
                _require(_minutes(start) < _minutes(end), f"Meeting must end after it starts at {meeting_prefix}")
        selected_group_id = course.get("selected_group_id")
        _require(selected_group_id is None or selected_group_id in group_ids, f"Unknown selected session group for {course_id}")

    status = data.get("offerings_status", "available")
    _require(status in {"available", "partial", "unavailable"}, "Invalid offerings_status")
    if status == "unavailable":
        _require(not courses, "Unavailable offerings must not contain fallback courses")
    audit = data.get("catalog_audit")
    if status in {"available", "partial"}:
        _require(isinstance(audit, dict), "catalog_audit is required for published offerings")
        visible_total = audit.get("visible_total")
        collected_count = audit.get("collected_count")
        audit_ids = audit.get("course_ids")
        _require(isinstance(visible_total, int) and visible_total >= 0, "catalog_audit.visible_total is invalid")
        _require(isinstance(collected_count, int) and collected_count >= 0, "catalog_audit.collected_count is invalid")
        _require(isinstance(audit_ids, list) and len(audit_ids) == len(set(audit_ids)), "catalog_audit.course_ids must be unique")
        _require(collected_count == len(audit_ids), "catalog_audit.collected_count does not match course_ids")
        _require(collected_count == visible_total, "Course catalogue pagination is incomplete")
        _require(audit.get("pagination_exhausted") is True, "Course catalogue last page was not verified")


def _walk_keys(value: Any) -> Iterable[str]:
    if isinstance(value, dict):
        for key, child in value.items():
            yield str(key)
            yield from _walk_keys(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_keys(child)


def _validate_source(source: Any, path: str) -> None:
    _require(isinstance(source, dict), f"{path} is required")
    _require(source.get("kind") in VALID_SOURCE_KINDS, f"Invalid {path}.kind")
    _require(isinstance(source.get("label"), str) and source["label"], f"{path}.label is required")
    observed = source.get("observed_at")
    _require(isinstance(observed, str) and observed, f"{path}.observed_at is required")
    try:
        dt.datetime.fromisoformat(observed.replace("Z", "+00:00"))
    except ValueError as exc:
        raise PlannerValidationError(f"{path}.observed_at must be an ISO date-time") from exc


def load_and_prepare(path: Path) -> dict[str, Any]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    safe = sanitize_personal_data(raw)
    validate_plan(safe)
    return safe


def _cli() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    next_parser = subparsers.add_parser("next-term", help="derive current and next TUM terms")
    next_parser.add_argument("--date", default=dt.date.today().isoformat(), help="ISO date, default: today")

    match_parser = subparsers.add_parser("match-program", help="match a program against a JSON list")
    match_parser.add_argument("query")
    match_parser.add_argument("programs", type=Path)

    validate_parser = subparsers.add_parser("validate", help="sanitize and validate a planner JSON file")
    validate_parser.add_argument("input", type=Path)

    args = parser.parse_args()
    if args.command == "next-term":
        result = planning_terms(dt.date.fromisoformat(args.date))
    elif args.command == "match-program":
        programs = json.loads(args.programs.read_text(encoding="utf-8"))
        if not isinstance(programs, list):
            raise PlannerValidationError("Program file must contain a JSON array")
        result = match_program(args.query, programs)
    else:
        result = load_and_prepare(args.input)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(_cli())
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(2)
